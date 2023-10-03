#!/usr/bin/env python
'''
glider_qc/glider_qc.py
'''
from cf_units import Unit
from netCDF4 import num2date, Dataset
# from ioos_qartod.qc_tests import qc
# from ioos_qartod.qc_tests import gliders as gliders_qc
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
        self.ncfile = ncfile
        if config_file is not None:
            self.load_config(config_file)

    def find_geophysical_variables(self):
        '''
        Returns a list of variable names matching the geophysical variable's
        standard names for temperature, conductivity, density and salinity.
        '''
        variables = []
        valid_standard_names = [
            'sea_water_temperature',
            'sea_water_electrical_conductivity',
            'sea_water_density',
            'sea_water_pressure',
            'sea_water_practical_salinity'
        ]

        for standard_name in valid_standard_names:
            ncvar = self.ncfile.get_variables_by_attributes(standard_name=standard_name)
            if len(ncvar) == 1:
                variables.append(ncvar[0].name)
        return variables

    # def find_qc_flags(self, ncvariable):
    #     '''
    #     Returns a list of non-GliderDAC QC flags associated with a variable
    #
    #     :param netCDF4.Variable ncvariable: Variable to get the status flag
    #                                         variables for
    #     '''
    #     valid_variables = []
    #     ancillary_variables = getattr(ncvariable, 'ancillary_variables', None)
    #     if isinstance(ancillary_variables, str):
    #         ancillary_variables = ancillary_variables.split(' ')
    #     else:
    #         return []
    #     for varname in ancillary_variables:
    #         if varname not in self.ncfile.variables:
    #             log.warning("%s defined as ancillary variable but doesn't exist", varname)
    #             continue
    #         anc_standard_name = getattr(self.ncfile.variables[varname],
    #                                     'standard_name', '')
    #         if varname.endswith('_qc'):
    #             valid_variables.append(varname)
    #         elif ("status_flag" in anc_standard_name or
    #               anc_standard_name.endswith("quality_flag")):
    #             valid_variables.append(varname)
    #
    #     return valid_variables

    def append_ancillary_variable(self, parent, child):
        '''
        Links two variables through the ancillary_variables attribute

        :param netCDF.Variable parent: Parent Variable
        :param netCDF.Variable child: Status Flag Variable
        '''

        ancillary_variables = getattr(parent, 'ancillary_variables', None)
        if isinstance(ancillary_variables, str) and len(ancillary_variables) > 0:
            ancillary_variables = ancillary_variables.split(' ')
        else:
            ancillary_variables = []
        ancillary_variables.append(child.name)
        parent.ancillary_variables = ' '.join(ancillary_variables)

    # def needs_qc(self, ncvariable):
    #     '''
    #     Returns True if the variable has no associated QC variables
    #
    #     :param netCDF4.Variable ncvariable: Variable to get the ancillary
    #                                         variables for
    #     '''
    #     ancillary_variables = self.find_qc_flags(ncvariable)
    #     return len(ancillary_variables) == 0

    # def create_qc_variables(self, ncvariable):
    #     '''
    #     Returns a list of variable names for the newly created variables for QC flags
    #     '''
    #     name = ncvariable.name
    #     standard_name = ncvariable.standard_name
    #     dims = ncvariable.dimensions
    #     log.info("Creating QARTOD variables for %s", name)
    #
    #     templates = {
    #         'flat_line': {
    #             'name': 'qartod_%(name)s_flat_line_flag',
    #             'long_name': 'QARTOD Flat Line Test for %(standard_name)s',
    #             'standard_name': 'flat_line_test_quality_flag',
    #             'flag_values': np.array([1, 2, 3, 4, 9], dtype=np.int8),
    #             'flag_meanings': 'GOOD NOT_EVALUATED SUSPECT BAD MISSING',
    #             'references': 'http://gliders.ioos.us/static/pdf/Manual-for-QC-of-Glider-Data_05_09_16.pdf',
    #             'qartod_test': 'flat_line',
    #             'dac_comment': 'ioos_qartod'
    #         },
    #         'gross_range': {
    #             'name': 'qartod_%(name)s_gross_range_flag',
    #             'long_name': 'QARTOD Gross Range Test for %(standard_name)s',
    #             'standard_name': 'gross_range_test_quality_flag',
    #             'flag_values': np.array([1, 2, 3, 4, 9], dtype=np.int8),
    #             'flag_meanings': 'GOOD NOT_EVALUATED SUSPECT BAD MISSING',
    #             'references': 'http://gliders.ioos.us/static/pdf/Manual-for-QC-of-Glider-Data_05_09_16.pdf',
    #             'qartod_test': 'gross_range',
    #             'dac_comment': 'ioos_qartod'
    #         },
    #         'rate_of_change': {
    #             'name': 'qartod_%(name)s_rate_of_change_flag',
    #             'long_name': 'QARTOD Rate of Change Test for %(standard_name)s',
    #             'standard_name': 'rate_of_change_test_quality_flag',
    #             'flag_values': np.array([1, 2, 3, 4, 9], dtype=np.int8),
    #             'flag_meanings': 'GOOD NOT_EVALUATED SUSPECT BAD MISSING',
    #             'references': 'http://gliders.ioos.us/static/pdf/Manual-for-QC-of-Glider-Data_05_09_16.pdf',
    #             'qartod_test': 'rate_of_change',
    #             'dac_comment': 'ioos_qartod'
    #         },
    #         'spike': {
    #             'name': 'qartod_%(name)s_spike_flag',
    #             'long_name': 'QARTOD Spike Test for %(standard_name)s',
    #             'standard_name': "spike_test_quality_flag",
    #             'flag_values': np.array([1, 2, 3, 4, 9], dtype=np.int8),
    #             'flag_meanings': 'GOOD NOT_EVALUATED SUSPECT BAD MISSING',
    #             'references': 'http://gliders.ioos.us/static/pdf/Manual-for-QC-of-Glider-Data_05_09_16.pdf',
    #             'qartod_test': 'spike',
    #             'dac_comment': 'ioos_qartod'
    #         },
    #         'pressure': {
    #             'name': 'qartod_monotonic_pressure_flag',
    #             'long_name': 'QARTOD Pressure Test for %(standard_name)s',
    #             'standard_name': 'quality_flag',
    #             'flag_values': np.array([1, 2, 3, 4, 9], dtype=np.int8),
    #             'flag_meanings': 'GOOD NOT_EVALUATED SUSPECT BAD MISSING',
    #             'references': 'http://gliders.ioos.us/static/pdf/Manual-for-QC-of-Glider-Data_05_09_16.pdf',
    #             'qartod_test': 'pressure',
    #             'dac_comment': 'ioos_qartod'
    #         },
    #         'primary': {
    #             'name': 'qartod_%(name)s_primary_flag',
    #             'long_name': 'QARTOD Primary Flag for %(standard_name)s',
    #             'standard_name': 'aggregate_quality_flag',
    #             'flag_values': np.array([1, 2, 3, 4, 9], dtype=np.int8),
    #             'flag_meanings': 'GOOD NOT_EVALUATED SUSPECT BAD MISSING',
    #             'references': 'http://gliders.ioos.us/static/pdf/Manual-for-QC-of-Glider-Data_05_09_16.pdf',
    #             'dac_comment': 'ioos_qartod_primary'
    #         }
    #     }
    #
    #     qcvariables = []
    #
    #     for tname, template in list(templates.items()):
    #         if tname == 'pressure' and standard_name != 'sea_water_pressure':
    #             continue
    #         variable_name = template['name'] % {'name': name}
    #
    #         if variable_name not in self.ncfile.variables:
    #             ncvar = self.ncfile.createVariable(variable_name, np.int8, dims, fill_value=np.int8(9))
    #         else:
    #             ncvar = self.ncfile.variables[variable_name]
    #
    #         ncvar.units = '1'
    #         ncvar.standard_name = template['standard_name'] % {'standard_name': standard_name}
    #         ncvar.long_name = template['long_name'] % {'standard_name': standard_name}
    #         ncvar.flag_values = template['flag_values']
    #         ncvar.flag_meanings = template['flag_meanings']
    #         ncvar.references = template['references']
    #         ncvar.dac_comment = template['dac_comment']
    #         if 'qartod_test' in template:
    #             ncvar.qartod_test = template['qartod_test']
    #         qcvariables.append(variable_name)
    #         self.append_ancillary_variable(ncvariable, ncvar)
    #
    #     return qcvariables

    def load_config(self, path='data/config_legacy_vars.yml'):
        '''
        Loads a yaml file configuration for QC
        '''
        path = path or 'data/config_legacy_vars.yml'
        log.info("Loading config from %s", path)
        with open(path, 'r') as f:
            self.config = yaml.safe_load(f.read())

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
        try:
            converted = Unit(units).convert(values, mapping[standard_name])
        except:
            log.exception("Normalizing %s", standard_name)
            raise
        return converted

    def apply_qc(self, ncpath, varname, configset):
        '''
        Pass configuration and netcdf file to ioos_qc to generate
        qc test results for a variable

        :param ncpath: string defining path to the netcdf file
        :param varname: string defining the variable name
        :param configset: dictionary with variable config specs for each QARTOD tests
        '''

        # Read the variable configuration specifications
        c = Config(configset)

        # Setup the stream
        # Use XarrayStream to extract numpy arrays from variables within a netCDF file
        # and passes them through as arrays to XarrayStream.
        qc = XarrayStream(ncpath)

        # Pass the run method and the config specs
        # Store as a list
        runner = list(qc.run(c))

        results = collect_results(runner, how='list')

        agg = CollectedResult(
            stream_id=varname,
            package='qartod',
            test='qc_rollup',
            function=aggregate,
            results=aggregate(results),
            tinp=qc.time(),
            data=qc.data(varname)
        )
        results.append(agg)

        return results
        
    # def apply_qc(self, ncvariable, parent):
    #     '''
    #     Applies QC to a qartod variable
    #
    #     :param netCDF4.Variable ncvariable: A QARTOD Variable
    #     '''
    #     qc_tests = {
    #         'flat_line': qc.flat_line_check,
    #         'gross_range': qc.range_check,
    #         'rate_of_change': qc.rate_of_change_check,
    #         'spike': qc.spike_check,
    #         'pressure': gliders_qc.pressure_check
    #     }
    #
    #     qartod_test = getattr(ncvariable, 'qartod_test', None)
    #     if not qartod_test:
    #         return
    #     standard_name = parent.standard_name
    #
    #     times, values, mask = self.get_unmasked(parent)
    #     # There's no data to QC
    #     if len(values) == 0:
    #         return
    #
    #     # If the config isn't set for this test, don't run it.
    #     if qartod_test not in self.config[standard_name]:
    #         return
    #
    #     test_params = {}
    #     if qartod_test in 'rate_of_change':
    #         times = ma.getdata(times[~mask])
    #         time_units = self.ncfile.variables['time'].units
    #         dates = np.array(num2date(times, time_units), dtype='datetime64[ms]')
    #         test_params['times'] = dates
    #         # Calculate the threshold value
    #         test_params['thresh_val'] = self.get_rate_of_change_threshold(values, times, time_units)
    #     elif qartod_test == 'spike':
    #         test_params['times'] = ma.getdata(times[~mask])
    #         test_params['low_thresh'], test_params['high_thresh'] = self.get_spike_thresholds(values)
    #     else:
    #         test_params = self.config[standard_name][qartod_test]
    #
    #     if qartod_test == 'pressure':
    #         test_params['pressure'] = values
    #     else:
    #         test_params['arr'] = values
    #
    #     qc_flags = qc_tests[qartod_test](**test_params)
    #     ncvariable[~mask] = qc_flags
    #
    #     for test_param in test_params:
    #         if test_param in ('arr', 'times', 'pressure'):
    #             continue
    #         ncvariable.setncattr(test_param, test_params[test_param])

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

        # Set the python time quantity
        time_quantity = pq.second  # Set default
        if 'minute' in time_units:
            time_quantity = pq.minute
        elif 'hour' in time_units:
            time_quantity = pq.hour
        elif 'day' in time_units:
            time_quantity = pq.day

        return thresh_rate / time_quantity

    def get_spike_thresholds(self, values):
        '''
        Return the min/max thresholds used for the spike test

        :param values: numpy array of values
        '''
        std = np.nanstd(values)
        min_thresh = 1.0 * std
        max_thresh = 2.0 * std
        return min_thresh, max_thresh

    def get_unmasked(self, ncvariable):
        times = self.ncfile.variables['time'][:]
        values = ncvariable[:]

        mask = np.zeros(times.shape[0], dtype=bool)

        if hasattr(values, 'mask'):
            mask |= values.mask

        if hasattr(times, 'mask'):
            mask |= times.mask

        values = ma.getdata(values[~mask])
        values = self.normalize_variable(values, ncvariable.units, ncvariable.standard_name)
        return times, values, mask

    def get_unmasked(self, ncvariable, times, values):

        mask = np.zeros(times.shape[0], dtype=bool)

        if hasattr(values, 'mask'):
            mask |= values.mask

        if hasattr(times, 'mask'):
            mask |= times.mask

        values = ma.getdata(values[~mask])
        times = ma.getdata(times[~mask])

        values = self.normalize_variable(values, ncvariable.units, ncvariable.standard_name)
        return times, values

    # def apply_primary_qc(self, ncvariable):
    #     '''
    #     Applies the primary QC array which is an aggregate of all the other QC
    #     tests.
    #
    #     :param netCDF4.Variable ncvariable: NCVariable
    #     '''
    #     primary_qc_name = 'qartod_%s_primary_flag' % ncvariable.name
    #     if primary_qc_name not in self.ncfile.variables:
    #         return
    #
    #     qcvar = self.ncfile.variables[primary_qc_name]
    #     # Only perform primary QC on variables created by DAC
    #     if getattr(qcvar, 'dac_comment', '') != 'ioos_qartod_primary':
    #         return
    #
    #     qc_variables = self.find_qc_flags(ncvariable)
    #     vectors = []
    #
    #     for qc_variable in qc_variables:
    #         ncvar = self.ncfile.variables[qc_variable]
    #         if getattr(ncvar, 'dac_comment', '') != 'ioos_qartod':
    #             continue
    #         log.info("Using %s in primary QC for %s", qc_variable, primary_qc_name)
    #         vectors.append(ma.getdata(ncvar[:]))
    #
    #     log.info("Applying QC for %s", primary_qc_name)
    #     flags = qc.qc_compare(vectors)
    #     qcvar[:] = flags

    def update_config(self, varspec, varname, times, values, time_units):
        '''
         Update the inout config file with specs values for the spike
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
        varspec['spike_test']['suspect_threshold'] = suspect_threshold
        varspec['spike_test']['fail_threshold'] = fail_threshold

        # Calculate the rate of change test threshold
        threshold = self.get_rate_of_change_threshold(values, times, time_units)
        # replace the threshold values in the config file
        varspec['rate_of_change_test']['threshold'] = threshold

        # Update the variable config specs
        configset = {'contexts': [{'streams': {varname: {'qartod': varspec}}}]}

        return configset

def qc_task(nc_path, config):
    '''
    Job wrapper around performing QC
    '''
    lock = lock_file(nc_path)
    if not lock.acquire():
        raise ProcessError("File lock already acquired by another process")
    try:
        with Dataset(nc_path, 'r+') as nc:
            run_qc(config, nc)
        os.setxattr(nc_path, "user.qc_run", b"true")
    except OSError:
        log.exception(f"Exception occurred trying to save QC to file on {nc_path}:")
    finally:
        lock.release()


def lock_file(path):
    '''
    Acquires a file lock or raises an exception
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


# def run_qc(config, ncfile):
#     '''
#     Runs QC on a netCDF file
#     '''
#     qc = GliderQC(ncfile, config)
#     for varname in qc.find_geophysical_variables():
#         log.info("Inspecting %s", varname)
#         ncvar = ncfile.variables[varname]
#
#         if not qc.needs_qc(ncvar):
#             log.info("%s does not need QARTOD", varname)
#             continue
#
#         for qcvarname in qc.create_qc_variables(ncvar):
#             log.info("Created QC Variable %s", qcvarname)
#             qcvar = ncfile.variables[qcvarname]
#
#             log.info("Applying QC for %s", qcvar.name)
#             qc.apply_qc(qcvar, ncvar)
#
#         qc.apply_primary_qc(ncvar)
#
#     # maybe unnecessary with calling context handler, but had some files
#     # which had xattr set, but not updated with QC
#     ncfile.sync()

def run_qc(config, ncfile):
    '''
    Runs IOOS QARTOD tests on a netCDF file
    '''
    xyz = GliderQC(ncfile, config)

    for var_name in xyz.find_geophysical_variables():
        log.info("Inspecting %s", var_name)

        # Extract data from the netCDF dataset
        var_data = ncfile.variables[var_name]
        timedata = ncfile.variables['time']
        time_units = timedata.units

        t = timedata[:]
        x = var_data[:]
        times, values = xyz.get_unmasked(var_data, t, x)

        if len(values) == 0:
            log.info(var_name, " is empty %s")
            continue

        # UPDATE VARIABLE CONFIG SET
        var_spec = xyz.config['contexts'][0]['streams'][var_name]['qartod']
        config_set = xyz.update_config(var_spec, var_name, times, values, time_units)
        print('updated config files')

        # Get the variable's qc results
        results = xyz.apply_qc(nc_path, var_name, config_set)
        print('applied qc')

        # Read the results and update the qartod variable
        for testname in ['gross_range_test', 'spike_test',
                         'rate_of_change_test', 'qc_rollup']:  # 'flat_line_test',

            qc_test = next(r for r in results if r.stream_id == var_name and r.test == testname)
            print('read qc results', var_name, testname)

            # create the qartod variable name and get the config specs
            if testname == 'qc_rollup':
                qartodname = 'qartod_' + var_name + '_primary_flag'
                # Pass the config specs to a variable
                testconfig = config_set['contexts'][0]['streams'][var_name]['qartod']
            else:
                qartodname = 'qartod_' + var_name + '_' + testname.split('_test')[0] + '_flag'
                # Pass the config specs to a variable
                testconfig = config_set['contexts'][0]['streams'][var_name]['qartod'][testname]

            print('created qartod name and got the config specs')

            # Update the qartod variable
            qartod_var = ncfile.variables[qartodname]
            qartod_var[:] = np.array(qc_test.results)
            qartod_var.qartod_test = repr(testname)
            ncfile.variables[qartodname].qartod_config = repr(testconfig)

            print('Updated the qartod variable')

            # add qartod variables to the variable ancillary_variables attribute
            xyz.append_ancillary_variable(var_data, qartod_var)
            print('Updated ancillary variable', var_name)

    # maybe unnecessary with calling context handler, but had some files
    # which had xattr set, but not updated with QC
    ncfile.sync()

def check_needs_qc(nc_path):
    '''
    Returns True if the netCDF file needs GliderQC
    '''
    # quick check to see if QC has already been run on these files
    try:
        if os.getxattr(nc_path, "user.qc_run"):
            return False
    except OSError:
        pass
    # with Dataset(nc_path, 'r') as nc:
    #     qc = GliderQC(nc, None)
    #     for varname in qc.find_geophysical_variables():
    #         ncvar = nc.variables[varname]
    #         if qc.needs_qc(ncvar):
    #             return True
    # if this section was reached, QC has been run, but xattr remains unset
    try:
        os.setxattr(nc_path, "user.qc_run", b"true")
    except OSError:
        log.exception(f"Exception occurred trying to set xattr on already QCed file at {ncfile.filepath()}:")
    return False
