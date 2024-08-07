#!/usr/bin/env python
'''
Runs IOOS QARTOD tests on a netCDF file
glider_qc/glider_qc.py
'''
from cf_units import Unit
from netCDF4 import num2date, Dataset
import datetime
from ioos_qc.qartod import aggregate
from ioos_qc.streams import XarrayStream
from ioos_qc.results import collect_results, CollectedResult
from ioos_qc.config import Config
import numpy as np
import numpy.ma as ma
import quantities as pq
import yaml
import logging
import redis
import os
import hashlib
log = logging.getLogger(__name__)
__RCONN = None


class ProcessError(ValueError):
    pass

class GliderQC(object):
    def __init__(self, ncfile, config_file=None):
        '''
        :param ncfile: netCDF4._netCDF4.Dataset
        :param config_file : json file
        '''
        self.ncfile = ncfile
        if config_file is not None:
            self.load_config(config_file)

    def needs_qc(self, ncvariable):
        '''
        Returns True if the variable has no associated QC variables

        :ncvariable: netCDF4.Variable
        '''
        ancillary_variables = self.find_qc_flags(ncvariable)
        log.info("Need QC: %s",len(ancillary_variables) == 0)

        return len(ancillary_variables) == 0

    def find_qc_flags(self, ncvariable):
        '''
        Returns a list of QARTOD flags associated with a variable

        :ncvariable: netCDF4.Variable
        '''
        valid_variables = []
        try:
            ancillary_variables = getattr(ncvariable, 'ancillary_variables', None)
        except:
            return []

        if isinstance(ancillary_variables, str) and len(ancillary_variables) > 0 and ancillary_variables !=  ' ':
            ancillary_variables = ancillary_variables.split(' ')
        else:
            log.info('ancillary_variables is empty or contains an empty string')
            return []

        for varname in ancillary_variables:
            if varname not in self.ncfile.variables:
                log.warning("%s defined as ancillary variable but doesn't exist", varname)

            if varname.startswith("qartod"):
                valid_variables.append(varname)

        return valid_variables

    def create_qc_variables(self, ncvariable):
        '''
        Returns a list of variable names for the newly created variables for QC flags
        '''
        name = ncvariable.name
        standard_name = ncvariable.standard_name
        dims = ncvariable.dimensions

        templates = {
            'flat_line': {
                'name': 'qartod_%(name)s_flat_line_flag',
                'long_name': 'QARTOD Flat Line Test for %(standard_name)s',
                'standard_name': 'flat_line_test_quality_flag',
            },
            'gross_range': {
                'name': 'qartod_%(name)s_gross_range_flag',
                'long_name': 'QARTOD Gross Range Test for %(standard_name)s',
                'standard_name': 'gross_range_test_quality_flag',
            },
            'rate_of_change': {
                'name': 'qartod_%(name)s_rate_of_change_flag',
                'long_name': 'QARTOD Rate of Change Test for %(standard_name)s',
                'standard_name': 'rate_of_change_test_quality_flag'
            },
            'spike': {
                'name': 'qartod_%(name)s_spike_flag',
                'long_name': 'QARTOD Spike Test for %(standard_name)s',
                'standard_name': "spike_test_quality_flag",
            },
            'primary': {
                'name': 'qartod_%(name)s_primary_flag',
                'long_name': 'QARTOD Primary Flag for %(standard_name)s',
                'standard_name': 'aggregate_quality_flag'
            }
        }

        qcvariables = []

        for tname, template in list(templates.items()):

            variable_name = template['name'] % {'name': name}

            if variable_name not in self.ncfile.variables:
                ncvar = self.ncfile.createVariable(variable_name, np.int8, dims, fill_value=np.int16(-999))
            else:
                ncvar = self.ncfile.variables[variable_name]

            ncvar.units = '1'
            ncvar.standard_name = template['standard_name'] % {'standard_name': standard_name}
            ncvar.long_name = template['long_name'] % {'standard_name': standard_name}
            ncvar.flag_values = np.array([1, 2, 3, 4, 9], dtype=np.int8)
            ncvar.valid_min = np.int8(1)
            ncvar.valid_max = np.int8(9)
            ncvar.flag_meanings = 'PASS NOT_EVALUATED SUSPECT FAIL MISSING'
            ncvar.references = 'http://gliders.ioos.us/static/pdf/Manual-for-QC-of-Glider-Data_05_09_16.pdf',
            ncvar.qartod_package = 'https://github.com/ioos/ioos_qc/blob/main/ioos_qc/qartod.py'
            ncvar.dac_comment = 'ioos_qartod'
            ncvar.ioos_category = 'Quality'

            qcvariables.append(variable_name)
            self.append_ancillary_variable(ncvariable, ncvar)

        return qcvariables

    def load_config(self, path):
        '''
        Loads a yaml file configuration for QC
        '''
        path = path or '/data/qc_config.yml'
        log.info("Loading config from %s", path)
        with open(path, 'r') as f:
            self.config = yaml.safe_load(f.read())

    def find_geophysical_variables(self):
        '''
        Returns a list of variable names matching the geophysical variable's
        standard names for temperature, conductivity, density and salinity.
        '''

        valid_standard_names = [
            'sea_water_temperature',
            'sea_water_electrical_conductivity',
            'sea_water_density',
            'sea_water_pressure',
            'sea_water_practical_salinity']

        variables = []
        note = ''
        for standard_name in valid_standard_names:
            ncvar = self.ncfile.get_variables_by_attributes(standard_name=standard_name)
            if len(ncvar) == 1:
                variables.append(ncvar[0].name)
            else:
                var_name = []
                for nn in range(len(ncvar)):
                    var_name.append(ncvar[nn].name)
                log.info("QC skipped for %s: more variables (%s) share the same standard name", standard_name, var_name)
                note += 'QC skipped for' + standard_name + ': the same standard name is shared by ' + ' '.join(var_name) + ', '

        return variables, note

    def get_unmasked(self, ndata):

        xdata = ndata[:]
        mask = np.zeros(xdata.shape[0], dtype=bool)

        if hasattr(xdata, 'mask'):
            mask |= xdata.mask

        vdata = ma.getdata(xdata[~mask])

        return vdata

    def get_rate_of_change_threshold(self, values, times, time_units='seconds since 1970-01-01T00:00:00Z'):
        '''
        Return the threshold used for the rate of change test

        :param values: numpy array of values
        :param times: numpy array of times
        :param time_units: string defining time units
        '''
        n_dev = 3   # Set to 3 standard deviations
        std = np.nanstd(values)
        thresh = n_dev * std
        thresh_rate = thresh / np.median(np.diff(times))

        return thresh_rate

    def get_spike_thresholds(self, values):
        '''
        Return the min/max thresholds used for the spike test
        :param values: numpy array of values
        '''
        std = np.nanstd(values)
        min_thresh = np.float64(1.0 * std)
        max_thresh = np.float64(2.0 * std)

        return min_thresh, max_thresh

    @classmethod
    def normalize_variable(cls, values, units, standard_name):
        '''
        Returns an array of values that are converted into a standard set of
        units. The motivation behind this is so that we compare values of the
        same units when performing QC.
        '''
        mapping = {
            'sea_water_temperature': 'deg_C',
            'sea_water_electrical_conductivity': 'S m-1',
            'sea_water_salinity': '1',
            'sea_water_practical_salinity': '1',
            'sea_water_pressure': 'dbar',
            'sea_water_density': 'kg m-3'
        }

        if units == 'psu': units = '1'
        try:
            converted = Unit(units).convert(values, mapping[standard_name])
        except:
            raise

        return converted

    def append_ancillary_variable(self, parent, child):
        '''
        Links two variables through the ancillary_variables attribute

        :param netCDF.Variable parent: Parent Variable
        :param netCDF.Variable child: Status Flag Variable
        '''
        # Case when ancillary_variables is not an attribute of the parent variable
        try:
            ancillary_variables = getattr(parent, 'ancillary_variables', None)
        except:
            parent.ancillary_variables = []

        if isinstance(ancillary_variables, str) and len(ancillary_variables) > 0:
            ancillary_variables = ancillary_variables.split(' ')
        else:
            ancillary_variables = []

        ancillary_variables.append(child.name)
        parent.ancillary_variables = ' '.join(ancillary_variables)

    def update_config(self, varspec, varname, times, values, time_units):
        '''
         Update the input config file with specs values for the spike
         and the gross range test methods

        :param varspec: Input dictionary with variable config specs for QARTOD tests
        :param varname: string defining the variable name
        :param times: numpy array of times
        :param values: numpy array of values
        :param time_units: string defining time units
        '''

        # Calculate the spike test threshold
        suspect_threshold, fail_threshold = self.get_spike_thresholds(values)
        # replace the threshold values in the config file
        varspec['spike_test']['suspect_threshold'] = np.float64(suspect_threshold)
        varspec['spike_test']['fail_threshold'] = np.float64(fail_threshold)

        # Calculate the rate of change test threshold
        threshold = self.get_rate_of_change_threshold(values, times, time_units)
        # replace the threshold values in the config file
        varspec['rate_of_change_test']['threshold'] = np.float64(threshold)

        # Update the variable config specs
        configset = {'contexts': [{'streams': {varname: {'qartod': varspec}}}]}

        return configset

    def apply_qc(self, nc_path, varname, configset):
        '''
        Pass configuration and netcdf file to ioos_qc to generate
        qc test results for a variable

        :param nc_path: string defining path to the netcdf file
        :param varname: string defining the variable name
        :param configset: dictionary with variable config specs for each QARTOD tests
        '''

        # Read the variable configuration specifications
        c_x = Config(configset)

        # Use XarrayStream to extract numpy arrays from variables within a netCDF file
        # and passes them through as arrays to XarrayStream.
        qc_x = XarrayStream(nc_path)

        # Pass the run method and the config specs
        # Store as a list
        runner = list(qc_x.run(c_x))

        # Create results
        results = collect_results(runner, how='list')

        # Add the qc_rollup results
        agg = CollectedResult(
            stream_id=varname,
            package='qartod',
            test='qc_rollup',
            function=aggregate,
            results=aggregate(results),
            tinp=qc_x.time(),
            data=qc_x.data(varname)
        )
        results.append(agg)

        return results

    def copy_variable(self, nc, ncvariable):
        '''
        Copy a variable to a new one
        :param nc: netCDF4._netCDF4.Dataset 
        :param ncvariable: netCDF4.Variable
        '''

        name = ncvariable.name
        typen = ncvariable.dtype
        dims = ncvariable.dimensions
        fval = ncvariable._FillValue
        
        new_name = name + '_obsolete'
        coord = name.split('_')[-1]
        
        ### Create a new variable with the same dimensions and attributes
        new_variable = nc.createVariable(new_name , typen, dims, fill_value=fval)

        # Copy the data
        new_variable[:] = ncvariable[:]

        # Copy attributes 
        listn = [item for item in ncvariable.ncattrs() if item != '_FillValue']
        for attr in listn:
            new_variable.setncattr(attr,  ncvariable.getncattr(attr))

        # Add comments
        new_variable.GDAC_comment = f" This is the original data made obsolete because it is 3 standard deviations \
        above the mean of the average {coord} array, classifying it as an outlier. The variable {name} has the corrected data."
                                
        return new_variable

    def check_location(self, ncf, report):
        '''
        Check the glider track lon and lat coordinates for outliers.
        If an outlier is detected:
         - Copy the profile_lat/lon variables onto new variables to preserve the original data.
         - Replace the profile_lat/lon data with the median of the lat or lon arrays.  
        :param ncf: netCDF4._netCDF4.Dataset 
        :param report: string reporting on issues
        '''
        profile_lat = ncf.variables['profile_lat']
        profile_lon = ncf.variables['profile_lon']

        lat = ncf.variables['lat']
        lon = ncf.variables['lon']

        if  ~np.isnan(profile_lat[:]) \
            or ~np.isnan(profile_lon[:]):

            ### Calculate how many standard deviations a value is above the mean
            num_std_lat = np.abs((profile_lat[:] - np.mean(lat[:])) / np.std(lat[:]))
            num_std_lon = np.abs((profile_lon[:] - np.mean(lon[:])) / np.std(lon[:]))

            if num_std_lat > 3 or num_std_lon > 3:
                log.info("Error in glider track lon and lat coordinates %s %s", profile_lat[:], profile_lon[:])
                report += "Error in glider track lon and lat coordinates, "

                ### Create new variables to store the data before it gets modified
                new_lat_variable = self.copy_variable(ncf, profile_lat)
                new_lon_variable = self.copy_variable(ncf, profile_lon)
                           
                ### Modify the data  
                profile_lat.comment = f"Value is an estimate of the latitude at the statistical median of the profile"             
                profile_lat.GDAC_comment = \
                    f"The original value {str(profile_lat[:])} was replaced with the median value of the lat array because it is 3 standard deviations above the mean of the average lat array, classifying it as an outlier"  
                profile_lat[:] = np.median(lat[:]) 

                ### Modify the profile_lon data                                                     
                profile_lon.comment = f"Value is an estimate of the longitude at the statistical median of the profile" 
                profile_lon.GDAC_comment = \
                    f"The original value {str(profile_lon[:])} was replaced with the median value of the lon array because it is 3 standard deviations above the mean of the average lon array, classifying it as an outlier"                                                                                           
                profile_lon[:] = np.median(lon[:])

        return report


    def check_time(self, ncfile, nc_path):
        '''
        Check the time array for data start time inconsistent with the deployment start time,
        invalid timestamps, duplicate timestamps, and non-ascending timestamps
       
        :param ncfile: netCDF4._netCDF4.Dataset 
        :param nc_path string defining path to the netcdf file
        '''

        times = ncfile.variables['time']
        timedata = self.get_unmasked(times)

        deployment_time = nc_path.split('/')[-2].split('-')[-1]

        report = ''
        try:
            start_time = datetime.datetime.strptime(deployment_time, '%Y%m%dT%H%M').timestamp()
            if start_time > timedata[:][0]:
                log.info("Start time starts before deployment time")
                report += "Start time starts before deployment time, "
        except:
            log.info("Missing Deployment Start time")
            report += "Missing Deployment Start time, "
            start_time = timedata[:][0]

        if np.any(timedata[:] == 0):
            log.info("Invalid timestamps (t == 0)")
            report += "Invalid timestamps (t == 0), "

        if len(timedata[:]) != len(set(timedata[:])):
            log.info("Duplicate timestamps")
            report += "Duplicate timestamps, "

        a = np.where(timedata[:-1] - timedata[1:] > 0)
        if len(a[0]) != 0:
            log.info("Not in Ascending Order")
            report += "Not in Ascending Order, "

        return report

# the main function
def run_qc(config, ncfile, nc_path): #
    '''
    Runs IOOS QARTOD tests on a netCDF file

    :param config: string defining path to the configuration file
    :param nc_path: string defining path to the netcdf file
    :param ncfile: netCDF4._netCDF4.Dataset
    '''
    xyz = GliderQC(ncfile, config)
    

    timedata = ncfile.variables['time']
    time_units = timedata.units

    
    # Check the Time Array
    report = xyz.check_time(ncfile, nc_path)


    if len(report) == 0:

        # Check glider track coordinates
        report = xyz.check_location(ncfile, report)

        # Loop through the legacy variables
        legacy_variables, note = xyz.find_geophysical_variables()

        # Report legacy variables issues
        if len(note) != 0:
            report += note

        # Apply QC to legacy variable
        for var_name in legacy_variables:
            var_data = ncfile.variables[var_name]

            # Check the Data Array
            if len(np.unique(var_data)) == 1:
                if np.ma.isMaskedArray(np.unique(var_data)) | np.isnan(np.unique(var_data)):
                    log.info("%s : The array is nans %s", var_name, np.unique(var_data))
                    text_n = 'Skipped QC: ' + var_name + ' is an array of nans'
                    report += text_n
                    continue

                if np.unique(var_data) == var_data._FillValue:
                    log.info("%s : The array is FillValues %s", var_name, np.unique(var_data))
                    text_n = 'Skipped QC: ' + var_name + ' is an array of FillValues'
                    report += text_n
                    continue

            values = xyz.get_unmasked(var_data)
            times = xyz.get_unmasked(timedata)

            try:
                values = xyz.normalize_variable(values, var_data.units, var_data.standard_name)
            except:
                log.exception("cf_units Problem Normalizing %s %s %s",  var_data.name, var_data.units, var_data.standard_name)
                repot += "cf_units Problem Normalizing" + var_data.name + var_data.units + var_data.standard_name
                raise

            # Create the QARTOD variables
            qcvarname = xyz.create_qc_variables(var_data)
            log.info("Created %s QC Variables for %s", str(len(qcvarname)), var_name)

            # UPDATE VARIABLE CONFIG SET
            var_spec = xyz.config['contexts'][0]['streams'][var_name]['qartod']
            config_set = xyz.update_config(var_spec, var_name, times, values, time_units)

            # GET the QC RESULTS
            results = xyz.apply_qc(nc_path, var_name, config_set)
            log.info("Generated QC test results for %s", var_name)

            for testname in ['gross_range_test',
                             'spike_test',
                             'rate_of_change_test',
                             'flat_line_test',
                             'qc_rollup']:

                qc_test = next(r for r in results if r.stream_id == var_name and r.test == testname)

                # create the qartod variable name and get the config specs
                if testname == 'qc_rollup':
                    qartodname = 'qartod_'+ var_name + '_primary_flag'
                    # Pass the config specs to a variable
                    testconfig = config_set['contexts'][0]['streams'][var_name]['qartod']
                else:
                    qartodname = 'qartod_'+ var_name + '_'+ testname.split('_test')[0]+'_flag'
                    # Pass the config specs to a variable
                    testconfig = config_set['contexts'][0]['streams'][var_name]['qartod'][testname]

                # Update the qartod variable
                log.info("Updating %s", qartodname)
                qartod_var = ncfile.variables[qartodname]
                qartod_var[:] = np.array(qc_test.results)
                qartod_var.qartod_test = f"{testname}"   
                ncfile.variables[qartodname].qartod_config = "{" + ", ".join(f"{key}: {value}" for key, value in testconfig.items()) + "}"

        ncfile.dac_qc_comment = report
        # maybe unnecessary with calling context handler, but had some files
        # which had xattr set, but not updated with QC
        ncfile.sync()

def qc_task(nc_path, config):
    '''
    Job wrapper around performing QC

    :param nc_path: string defining path to the netcdf file
    :param config: string defining path to the configuration file
    '''
    lock = lock_file(nc_path)
    if not lock.acquire():
        raise ProcessError("File lock already acquired by another process")
    # Repeat xattr check.  Consider removing when inotify loop conditions
    # where file is repeteadly picked are addressed.
    try:
        if os.getxattr(nc_path, "user.qc_run"):
            return False
    except OSError:
        pass
    try:
        with Dataset(nc_path, 'r+') as nc:
            run_qc(config, nc, nc_path)
        os.setxattr(nc_path, "user.qc_run", b"true")
    except OSError:
        log.exception(f"Exception occurred trying to save QC to file on {nc_path}:")
    finally:
        lock.release()

def lock_file(path):
    '''
    Acquires a file lock or raises an exception

    :param nc_path string defining path to the netcdf file
    '''
    rc = get_redis_connection()
    digest = hashlib.sha1(path.encode("utf-8")).hexdigest()
    key = 'gliderdac:%s' % digest
    lock = rc.lock(key, blocking_timeout=60)
    return lock

def get_redis_connection():
    '''
    Returns a redis connection configured with a pool. Redis can be configured
    from the environment variables REDIS_HOST, REDIS_PORT and REDIS_DB
    '''
    global __RCONN
    if __RCONN is not None:
        return __RCONN
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = os.environ.get('REDIS_PORT', 6379)
    redis_db = os.environ.get('REDIS_DB', 0)
    redis_pool = redis.ConnectionPool(host=redis_host,
                                      port=redis_port,
                                      db=redis_db)
    __RCONN = redis.Redis(connection_pool=redis_pool)
    return __RCONN

def check_needs_qc(nc_path):
    '''
    Returns True if the netCDF file needs GliderQC

    param nc_path: string defining path to the netcdf file
    '''
    # quick check to see if QC has already been run on these files
    try:
        if os.getxattr(nc_path, "user.qc_run"):
            return False
    except OSError:
        log.exception(f"Exception occurred trying to get xattr at {nc_path}:")
        pass
    with Dataset(nc_path, 'r') as nc:
        qc = GliderQC(nc, None)
        legacy_var, note = qc.find_geophysical_variables()
        for varname in legacy_var:
            ncvar = nc.variables[varname]
            if qc.needs_qc(ncvar):
                return True
    # if this section was reached, QC has been run, but xattr remains unset
    try:
        os.setxattr(nc_path, "user.qc_run", b"true")
    except OSError:
        log.exception(f"Exception occurred trying to set xattr on already QCed file at {nc_path}:")
    return False
