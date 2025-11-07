#!/usr/bin/env python
'''
Runs IOOS QARTOD tests on a netCDF file
glider_qc/glider_qc.py
'''
from cf_units import Unit
from netCDF4 import num2date, Dataset
import datetime
from ioos_qc.stores import PandasStore
from ioos_qc.streams import PandasStream
from ioos_qc.results import collect_results, CollectedResult
from ioos_qc.config import Config
import numpy as np
import pandas as pd
import json
import math
import numpy.ma as ma
import quantities as pq
import yaml
import logging
import redis
import os
import hashlib
from shapely.geometry import Point, Polygon
log = logging.getLogger(__name__)
__RCONN = None


class ProcessError(ValueError):
    pass

class GliderQC(object):
    def __init__(self, ncfile, config_file=None):
        '''
        Initializes an instance of the class with a netCDF file and an optional config file.

        :param ncfile: The netCDF file to be used (required).
        :param config_file: The path to a configuration file (optional).
        '''
        self.ncfile = ncfile

        if config_file is not None:
            try:
                self.load_config(config_file)
            except Exception as e:
                log.error("Error loading config file %s: %s", config_file, str(e))

    def needs_qc(self, ncvariable):
        '''
        Returns True if the variable has no associated QC variables

        :param ncvariable: netCDF4.Variable
        '''
        ancillary_variables = self.find_qc_flags(ncvariable)
        if not ancillary_variables:
            log.info("No QARTOD flags found for %s, QC is needed", ncvariable.name)
        else:
            log.info("QARTOD flags found for %s", ncvariable.name)

        # Return True if ancillary_variables is empty, otherwise False
        return not ancillary_variables

    def find_qc_flags(self, ncvariable):
        '''
        Returns a list of QARTOD flags associated with a variable

        :param ncvariable: netCDF4.Variable
        '''

        valid_variables = []

        # Process the ancillary_variables if it's a valid non-empty string
        ancillary_variables = getattr(ncvariable, 'ancillary_variables', None)
        if isinstance(ancillary_variables, str) and ancillary_variables.strip():
            ancillary_variables = ancillary_variables.split()
        else:
            log.info("%s ancillary_variables is not a valid string or is empty", ncvariable.name)
            return []

        # Check each variable name in ancillary_variables
        for varname in ancillary_variables:
            if varname.startswith('qartod'):
                # Check if the variable exists in the file
                if varname not in self.ncfile.variables:
                    log.warning("Skipped %s variable it is not found in the file", varname)
                    # Skip this variable and do not add it to valid_variables
                    continue
                # Add the valid varname to the list
                valid_variables.append(varname)

        return valid_variables

    def create_qc_variables(self, ncvariable):
        '''
        Returns a list of variable names for the newly created variables for QC flags

        :param ncvariable: netCDF4.Variable
        '''
        name_value = ncvariable.name
        standard_name_value = ncvariable.standard_name
        dims = ncvariable.dimensions

        templates = {
            'flat_line': {
                'name': 'qartod_{name}_flat_line_flag',
                'long_name': 'QARTOD Flat Line Test for {standard_name}',
                'standard_name': 'flat_line_test_quality_flag',
            },
            'gross_range': {
                'name': 'qartod_{name}_gross_range_flag',
                'long_name': 'QARTOD Gross Range Test for {standard_name}',
                'standard_name': 'gross_range_test_quality_flag',
            },
            'rate_of_change': {
                'name': 'qartod_{name}_rate_of_change_flag',
                'long_name': 'QARTOD Rate of Change Test for {standard_name}',
                'standard_name': 'rate_of_change_test_quality_flag'
            },
            'spike': {
                'name': 'qartod_{name}_spike_flag',
                'long_name': 'QARTOD Spike Test for {standard_name}',
                'standard_name': "spike_test_quality_flag",
            },
            'primary': {
                'name': 'qartod_{name}_primary_flag',
                'long_name': 'QARTOD Primary Flag for {standard_name}',
                'standard_name': 'aggregate_quality_flag'
            }
        }

        qcvariables = []

        for tname, template in list(templates.items()):

            variable_name = template['name'].format(name=name_value)

            if variable_name not in self.ncfile.variables:
                ncvar = self.ncfile.createVariable(variable_name, np.int8, dims, fill_value=np.int16(-999))
            else:
                ncvar = self.ncfile.variables[variable_name]

            ncvar[:] = np.full(len(ncvariable[:]), 2)
            ncvar.units = '1'
            ncvar.standard_name = template['standard_name']
            ncvar.long_name = template['long_name'].format(standard_name=standard_name_value)
            ncvar.flag_values = np.array([1, 2, 3, 4, 9], dtype=np.int8)
            ncvar.valid_min = np.int8(1)
            ncvar.valid_max = np.int8(9)
            ncvar.flag_meanings = 'PASS NOT_EVALUATED SUSPECT FAIL MISSING'
            ncvar.references = 'https://gliders.ioos.us/files/Manual-for-QC-of-Glider-Data_05_09_16.pdf '
            ncvar.qartod_package = 'https://github.com/ioos/ioos_qc/blob/main/ioos_qc/qartod.py'
            ncvar.dac_comment = 'QARTOD TEST RUN'
            ncvar.ioos_category = 'Quality'

            qcvariables.append(variable_name)
            self.append_ancillary_variable(ncvariable, ncvar)

        return qcvariables

    def load_config(self, path=None):
        '''
        Loads a YAML file configuration for QC.

        :param path: string (optional) - the path to the YAML config file.
                     If no path is provided, defaults to '/data/qc_config.yml'.
        :raises FileNotFoundError: If the file cannot be found at the specified path.
        :raises yaml.YAMLError: If the file contains invalid YAML.
        '''
        path = path or '/data/qc_config.yml'
        log.info("Loading config from %s", path)
        try:
            with open(path, 'r') as f:
                self.config = yaml.safe_load(f.read())
        except FileNotFoundError:
            log.error("Config file not found at %s", path)
        except yaml.YAMLError as e:
            log.error("Error loading YAML file %s: %s", path, e)

    def find_geophysical_variables(self):
        '''
        Returns a list of variable names matching the geophysical variable's
        standard names for temperature, conductivity, density and salinity.

        :return string of variables name to use for qc
        :return string of report_list with encountered issues
        '''
        valid_standard_names = [
            'sea_water_temperature',
            'sea_water_electrical_conductivity',
            'sea_water_density',
            'sea_water_pressure',
            'sea_water_practical_salinity']

        variables = []
        report_list = []
        for standard_name in valid_standard_names:
            # Get variables matching the standard name
            ncvar = self.ncfile.get_variables_by_attributes(standard_name=standard_name)
            if ncvar:
                if len(ncvar) == 1:
                    # If only one variable with this standard name, add it to the list
                    variables.append(ncvar[0].name)
                else:
                    # If multiple variables with the same standard name, log the conflict
                    var_names = [var.name for var in ncvar]
                    log.info("QC skipped for %s: %s variables share the same standard_name", standard_name, var_names)
                    # Build a note for the QC skip situation
                    report_list.append(f"more than one variable shared {standard_name}")
            else:
                log.info('No variables found with standard_name %s', standard_name)
                report_list.append(f"no variable found with {standard_name}")

        return variables, ' '.join(report_list)

    def get_rate_of_change_threshold(self, values, times):
        '''
        Return the threshold used for the rate of change test
        This function calculates the maximum rate of change between consecutive values
        within one standard deviation of the mean.

        :param values: numpy array of values
        :param times: numpy array of times

        :return: float value representing the maximum rate of change
        :return: string of report_list of encountered issues
        '''
        report_list = []
        if len(values) < 2 or len(times) < 2:
            log.info("Insufficient data: both 'values' and 'times' must have at least two elements.")
            report_list.append("Insufficient data: both 'values' and 'times' must have at least two elements.")
            return None, ' '.join(report_list)

        if np.sum(~np.isnan(values)) > 1:  # Check if there are at least 2 valid values
            std = np.nanstd(values)
            mean = np.nanmean(values)
        else:
            report_list.append("Not enough valid data points for std and mean calculations.")
            return None, ' '.join(report_list)

        list_values = []
        list_times = []
        for nn, xx in enumerate(values):
            if (xx > (mean - std)) and (xx < (mean+std)):
                list_values.append(values[nn])
                list_times.append(times[nn])

        # Ensure there are enough data points to compute the rate of change
        if len(list_values) < 2:
            log.info("Insufficient data: both 'values' and 'times' must have at least two elements.")
            report_list.append("Insufficient data: both 'values' and 'times' must have at least two elements.")
            return None, ' '.join(report_list)

        # Calculate the rate of change as absolute difference between consecutive values
        roc = np.abs(np.diff(list_values) / np.diff(list_times).astype(float))

        # Return the maximum rate of change
        threshold = np.max(roc)

        return threshold, ' '.join(report_list)

    def get_spike_thresholds(self, values):
        '''
        Return the min/max thresholds used for the spike test.

        :param values: numpy array of values

        :return: tuple of (suspect_threshold, fail_threshold) as np.float64
        :return: string of report_list of encountered issues
        '''
        report_list = []
        # If values is not a numpy array, convert it to one
        if not isinstance(values, np.ndarray):
            values = np.asarray(values)

        # Check if there are at least 2 valid values
        # remove nan
        valid_values = [x for x in values if not np.isnan(x)]

        if len(valid_values) < 2:
            log.info("Not enough valid data for variance calculation.")
            report_list.append("Not enough valid data for std calculation.")
            return None, None, ' '.join(report_list)
        else:
            std = np.nanstd(valid_values)

        # Define the suspect and fail thresholds
        suspect_threshold = np.float64(1.0 * std)
        fail_threshold = np.float64(2.0 * std)

        return suspect_threshold, fail_threshold, ' '.join(report_list)

    @classmethod
    def normalize_variable(cls, values, units, standard_name):
        '''
        Returns an array of values that are converted into a standard set of
        units. The motivation behind this is so that we compare values of the
        same units when performing QC.

        :param values: numpy array of values
        :param units: string defining units
        :param standard_name: string defining the variable's CF compliant name

        :return report_list: a string logging issues encountered
        :return converted: numpy array of converted values
        '''
        report_list = []
        mapping = {
            'sea_water_temperature': 'deg_C',
            'sea_water_electrical_conductivity': 'S m-1',
            'sea_water_salinity': '1',
            'sea_water_practical_salinity': '1',
            'sea_water_pressure': 'dbar',
            'sea_water_density': 'kg m-3'
        }

        # Handle conversion of 'psu' to '1' for salinity
        if units == 'psu':
            units = '1'

        # Check if the standard name is in the mapping
        if standard_name not in mapping:
            log.info(f"Standard name '{standard_name}' not found in the mapping dictionary.")
            report_list.append(f"Standard name '{standard_name}' not found in the mapping dictionary.")
            return None, ' '.join(report_list)

        # Get the target unit for conversion
        target_unit = mapping[standard_name]
        try:
            # Perform the unit conversion (make sure the `Unit` class and its method are correct)
            converted = Unit(units).convert(values, target_unit)
        except Exception as e:
            # log in error if conversion fails
            log.info(f"Failed to convert units from '{units}' to '{target_unit}' for standard name '{standard_name}': {str(e)}")
            report_list.append(f"Failed to convert units from {str(units)} to {str(target_unit)} for standard name {standard_name}: {str(e)}")
            return None, ' '.join(report_list)

        return converted, ' '.join(report_list)

    def append_ancillary_variable(self, parent, child):
        '''
        Links two variables through the ancillary_variables attribute.

        :param parent: netCDF.Variable (Parent Variable)
        :param child: netCDF.Variable (Status Flag Variable)
        '''
        # Retrieve the current ancillary_variables, defaulting to an empty list if not set
        ancillary_variables = getattr(parent, 'ancillary_variables', None)

        # If ancillary_variables is a string, convert it into a list
        if isinstance(ancillary_variables, str):
            ancillary_variables = ancillary_variables.split()
        elif ancillary_variables is None:
            ancillary_variables = []

        # Add the child's name to the list of ancillary variables
        ancillary_variables.append(child.name)

        # Save the updated list back as a space-separated string
        parent.ancillary_variables = ' '.join(ancillary_variables)

    def update_config(self, varspec, varname, times, values, time_units):
        '''
         Update the input config file with specs values for the spike
         and the gross range test methods

        :param varspec: dictionary with variable config specs for QARTOD tests
        :param varname: string defining the variable name
        :param times: numpy array of times
        :param values: numpy array of values
        :param time_units: string defining time units

        :return dictionary with configuration specs for qc
        :return string report_list with encountered issues
        '''
        report_list = []
        # Calculate the spike test threshold
        # do not use the 1st and last data values in calculation
        values = values[1:-1]
        (suspect_threshold, fail_threshold, inote) = self.get_spike_thresholds(values)
        if suspect_threshold == None or fail_threshold == None:
            report_list.append(f"spike_test dropped for {varname}: {inote}")
            del varspec['spike_test']
        else:
            # replace the threshold values in the config file
            if 'rate_of_change_test' not in varspec:
                # If the key doesn't exist, initialize it as an empty dictionary or some default value
                varspec['spike_test'] = {}
            varspec['spike_test']['suspect_threshold'] = np.float64(suspect_threshold)
            varspec['spike_test']['fail_threshold'] = np.float64(fail_threshold)

        # Calculate the rate of change test threshold
        threshold, inote = self.get_rate_of_change_threshold(values, times)
        if threshold is None:
            report_list.append(f"rate_of_change_test dropped for {varname}: {inote}")
            del varspec['rate_of_change_test']
        else:
            # replace the threshold values in the config file
            if 'rate_of_change_test' not in varspec:
                # If the key doesn't exist, initialize it as an empty dictionary or some default value
                varspec['rate_of_change_test'] = {}
            varspec['rate_of_change_test']['threshold'] = np.float64(threshold)

        # Update the variable config specs
        configset = {'contexts': [{'streams': {varname: {'qartod': varspec}}}]}

        return configset, ' '.join(report_list)

    def apply_qc(self, df, varname, configset):
        '''
        Pass configuration and netCDF file to ioos_qc to generate
        QC test results for a variable

        :param nc_path: string defining path to the netCDF file
        :param varname: string defining the variable name
        :param configset: dictionary with variable config specs for each QARTOD test
        :return: List of QC results
        '''
        # Step 1: Load the variable configuration specifications
        c_x = Config(configset)  # Ensure that Config is correctly instantiated

        # Step 2: Pass the DataFrame into the PandasStream for processing
        try:
            qc_x = PandasStream(df)
        except Exception as e:
            log.error(f"Failed to read data for {varname} from {nc_path}: {e}")
            return []

        # Step 3: Run the QC tests
        try:
            results = qc_x.run(c_x)
        except Exception as e:
            log.error(f"Error running QC tests on {varname}: {e}")
            return []

        # Step 4: Store the results in another DataFrame
        try:
            store = PandasStore(results)
        except Exception as e:
            log.error(f"Error collecting QC results for {varname}: {e}")
            return []

        # Step 5: Compute any aggregations
        try:
            store.compute_aggregate(name='rollup_qc')  # Appends to the results internally
        except Exception as e:
            log.error(f"Error computing any aggregations for {varname}: {e}")
            return []

        # Step 6: Write only the test results to the store
        results_store = store.save(write_data=False, write_axes=False)

        return results_store

    def check_geophysical_variables(self, var_name):
        '''
        Check the data array for the specified geophysical variable.

        :param var_name: variable name (str)
        :return: report_list (str) containing encountered issues
        '''
        report_list = []

        # Access the variable
        inp = self.ncfile.variables[var_name]

        # Check if valid_min and valid_max are correctly ordered
        if inp.valid_min > inp.valid_max:
            log.info("%s: valid_min (%s) and valid_max (%s) are switched", inp.name, inp.valid_min, inp.valid_max)
            report_list.append(inp.name + ' has the valid_min and valid_max switched')
            return ' '.join(report_list)

        # Get unique values once
        unique_vals = np.unique(inp[:])

        # Check if all values in the array are the same
        if len(unique_vals) == 1:
            # Check if it's a masked array or an array of NaNs
            if np.ma.isMaskedArray(unique_vals) or np.isnan(unique_vals).all():
                log.info("%s: The array is NaNs %s", inp.name, unique_vals)
                report_list.append(inp.name + ' is an array of NaNs')
                return ' '.join(report_list)

            # Check if it's an array of fill values
            if unique_vals == inp._FillValue:
                log.info("%s: The array is fill values %s", inp.name, unique_vals)
                report_list.append(inp.name + 'is an array of fill values')
                return ' '.join(report_list)

        return ' '.join(report_list)

    def create_location_flag_variable(self, ndim, flag):
        '''
        Create a location test variable for the lon and lat coordinates.

        :param ndim: tuple or list, the dimensions of the netCDF variable (e.g., (time, lat, lon)).
        :param flag: integer, the flag value to assign to the location test variable.

        :returns: netCDF variable, the created location test flag variable.
        '''
        ncvar_name = 'qartod_location_test_flag'

        # Create the variable with int8 type and given dimensions
        ncvar = self.ncfile.createVariable(ncvar_name , np.int8, ndim, fill_value=np.int8(2))

        # Assign flag value to the whole array (assuming flag is a scalar)
        ncvar[:] = flag

        # Set additional attributes
        ncvar.units = '1'
        ncvar.standard_name = 'location_test_quality_flag'
        ncvar.long_name = 'QARTOD Location Flag for the profile_(lat, lon) variables'
        ncvar.flag_values = np.array([1, 2, 3, 4, 9], dtype=np.int8)
        ncvar.valid_min = np.int8(1)
        ncvar.valid_max = np.int8(9)
        ncvar.flag_meanings = 'PASS NOT_EVALUATED SUSPECT FAIL MISSING'
        ncvar.references = (
            'The GDAC uses a modified version of the location test described in '
            'https://gliders.ioos.us/files/Manual-for-QC-of-Glider-Data_05_09_16.pdf'
        )
        ncvar.qartod_module = (
            'The GDAC location test does not use the algorithm from '
            'https://github.com/ioos/ioos_qc/blob/main/ioos_qc/qartod.py (location_test) '
            'but instead relies on the statistical median of the lat/lon arrays'
        )
        ncvar.dac_comment = (
            'The FAIL flag is applied if the profile_(lat, lon) value exceeds 3 '
            'standard deviations above the mean of the average lat/lon arrays'
        )
        ncvar.ioos_category = 'Quality'

        return ncvar

    def check_location(self):
        '''
        Check the glider track lon and lat coordinates for outliers.
        If an outlier is detected:
            - Copy the profile_lat/lon variables onto new variables to preserve the original data.
            - Replace the profile_lat/lon data with the median of the lat or lon arrays.

        :return: report_list: string statement reporting on issues
        '''
        report_list = []
        profile_lat = self.ncfile.variables['profile_lat'][0]
        profile_lon = self.ncfile.variables['profile_lon'][0]
        lat = self.ncfile.variables['lat'][:]
        lon = self.ncfile.variables['lon'][:]

        # Check if lat/lon are not NaN or masked
        if not (np.isnan(profile_lat) or np.ma.is_masked(profile_lat) or np.isnan(profile_lon) or np.ma.is_masked(profile_lon)):
            poly = self.watch_circle(np.nanmean(lat), np.nanmean(lon), 2.0, num_points=72)
            set_flag = self.is_point_outside_polygon(profile_lat, profile_lon, poly)

            if set_flag:
                flag = 4  # FAIL
                log.info(f"profile_lat={profile_lat}, profile_lon={profile_lon} are outside the polygon")
                report_list.append("error in glider track lat/lon")
            else:
                flag = 1  # PASS
                report_list.append(f"profile_lat={profile_lat}, profile_lon={profile_lon} are inside the polygon")
        else:
            flag = 9  # MISSING
            report_list.append(f"profile_lat={profile_lat}, profile_lon={profile_lon} are missing")

        # Create location test variable to store the test flag
        ndim = self.ncfile.variables["profile_lat"].dimensions
        location_flag_variable = self.create_location_flag_variable(ndim, flag)

        # Store location test variable under the ancillary_variables attribute
        self.ncfile.variables['profile_lat'].ancillary_variables = location_flag_variable.name
        self.ncfile.variables['profile_lon'].ancillary_variables = location_flag_variable.name

        return ' '.join(report_list)

    def watch_circle(self, center_lat, center_lon, radius_miles, num_points=128):
        """
        Approximate a small geodesic circle around (center_lat, center_lon).
        Returns list of (lat, lon) tuples (closed: first == last).
        Suitable for small radii like 2 miles.
        """
        # 1 degree latitude ≈ 69.172 miles
        miles_per_deg_lat = 69.172
        delta_lat_deg = radius_miles / miles_per_deg_lat

        lat_rad = math.radians(center_lat)
        cos_lat = math.cos(lat_rad)
        # avoid zero
        miles_per_deg_lon = miles_per_deg_lat * max(abs(cos_lat), 1e-12)
        delta_lon_deg = radius_miles / miles_per_deg_lon

        points = []
        for i in range(num_points):
            theta = 2 * math.pi * i / num_points
            dlat = delta_lat_deg * math.sin(theta)
            dlon = delta_lon_deg * math.cos(theta)
            lat = center_lat + dlat
            lon = center_lon + dlon
            # normalize lon
            if lon > 180: lon -= 360
            if lon < -180: lon += 360
            points.append((lat, lon))
        points.append(points[0])
        return points

    def is_point_outside_polygon(self, point_lat, point_lon, polygon_points):
        '''
        polygon_points: list of (lat, lon) tuples (closed: first==last or not)
        shapely expects (lon, lat) ordering
        '''
        poly = Polygon([(lon, lat) for lat, lon in polygon_points])
        pt = Point(point_lon, point_lat)
        return not poly.contains(pt)

    def check_time(self, tnp, nc_path):
        '''
        Check the time array for data start time inconsistent with the deployment start time,
        invalid timestamps, duplicate timestamps, and non-ascending timestamps.

        :param tnp: time array (numpy.ma.core.MaskedArray)
        :param nc_path: netCDF file path (str)
        :return: report_list: string statement reporting on issues
        '''
        report_list = []
        # Check if any timestamps are masked
        if np.any(tnp.mask):
            log.info("Timestamps are masked")
            report_list("masked timestamps")
            return ' '.join(report_list)

        # Extract deployment start time from the nc_path
        deployment_time = nc_path.split('/')[-2].split('-')[-1]

        try:
            # Convert deployment time to a timestamp
            dp_time = datetime.datetime.strptime(deployment_time, '%Y%m%dT%H%M%S').timestamp()
            # Convert start_time to datetime64
            dp_time_dt = np.datetime64(datetime.datetime.fromtimestamp(dp_time))
            dp_time_dt = dp_time_dt.astype('datetime64[s]')
            # Check if the first timestamp in the data is before the deployment time
            if dp_time_dt > tnp[0]:
                log.info("Start time precedes deployment time")
                report_list.append("start time " + str(tnp[0]) + " precedes deployment time " + str(dp_time_dt))
                return ' '.join(report_list)
        except ValueError:
            # Handle invalid format for deployment time
            log.info("Missing or invalid Deployment Start time")
            report_list.append("deployment time not in %Y%m%dT%H%M%S format" + str(deployment_time))
            return ' '.join(report_list)

        # Check for invalid timestamps (e.g., timestamps with value 0)
        if np.any(tnp[:] == 0):
            log.info("Invalid timestamps (t == 0)")
            report_list.append("timestamps assigned a value of 0")
            return ' '.join(report_list)

        # Only consider valid (unmasked) values
        valid_values = tnp[~np.isnan(tnp)]

        # Check for duplicate timestamps
        if len(valid_values) != len(set(valid_values)):
            log.info("Duplicate timestamps")
            report_list.append("duplicate timestamps")
            return ' '.join(report_list)

        # Check if the timestamps are in ascending order
        # This will check if each timestamp is less than the next one
        # Ensure the array is of datetime64 type
        if valid_values.dtype != 'datetime64[s]':
            valid_values = valid_values.astype('datetime64[s]')

        if np.any(np.diff(valid_values) <= np.timedelta64(0, 's')):
            log.info("Not in Ascending Order")
            report_list.append("timestamps out of order")
            return ' '.join(report_list)

        return ' '.join(report_list)

# the main function
def run_qc(config, ncfile, ncfile_path):
    '''
    Runs IOOS QARTOD tests on a netCDF file

    :param config: string defining path to the configuration file
    :param ncfile_path: string defining path to the netCDF file
    :param ncfile: netCDF4._netCDF4.Dataset
    '''
    report_list = []
    xyz = GliderQC(ncfile, config)
    deployment_name = ncfile_path.split('/')[-2]
    file_name = ncfile_path.split('/')[-1]

    times = ncfile.variables['time']
    # Check Time
    try:
        inote = xyz.check_time(times[:].astype('datetime64[s]'), ncfile_path)
        report_list.append(inote)
    except Exception as e:
        time_err = "Could not check time."
        log.exception(f"{time_err}: {str(e)}")
        report_list.append(f"{time_err}: {str(e)}")

    # log time array issues
    report = ' '.join(report_list).strip()
    if len(report.strip()) != 0:
        ncfile.dac_qc_comment = str(deployment_name) + ' (' + str(file_name) + ': ' + report + ')'
    else:
        log.info(" Running IOOS QARTOD tests on %s", file_name)

        # Check Location (lat/lon)
        if 'qartod_location_test_flag' not in ncfile.variables:
            try:
                report_list.append(xyz.check_location())
            except Exception as e:
                location_err = "Could not check location."
                log.exception(f"{location_err}: {str(e)}")
                report_list.append(f"{location_err}: {str(e)}")

        # Find geophysical variables
        legacy_variables, note = xyz.find_geophysical_variables()
        if not legacy_variables:
            log.info("No variables found.")
            report_list.append("No variables found.")
        else:
            log.info("Found %s variables for QARTOD tests: %s", str(len(legacy_variables)), legacy_variables)
            # Report legacy variables issues
            report_list.append(note)

            # Loop through the legacy variables and apply QARTOD
            for var_name in legacy_variables:
                var_data = ncfile.variables[var_name]
                values = [x if x != '--' else np.nan for x in var_data[:]]

                # Create the QARTOD variables
                qcvarname = xyz.create_qc_variables(var_data)
                log.info("Created %s QC Variables for %s", str(len(qcvarname)), var_name)

                # Check the Data Array
                if xyz.check_geophysical_variables(var_name): #cfile,
                    report_list.append(xyz.check_geophysical_variables(var_name))
                    continue

                # Check the mapping of standard names with units
                try:
                    values, note = xyz.normalize_variable(np.array(values[:]), var_data.units, var_data.standard_name)
                    report_list.append(note)
                    if values is None:
                        continue
                except Exception as e:
                    unit_conversion_err = "Could not normalize data: unit conversion failed."
                    log.exception(f"{unit_conversion_err}: {str(e)}")
                    report_list.append(f"{unit_conversion_err}: {str(e)}")
                    continue

                # Update variable config set
                var_spec = xyz.config['contexts'][0]['streams'][var_name]['qartod']
                config_set, note = xyz.update_config(var_spec, var_name, times[:].astype('datetime64[s]'), values, times.units)
                report_list.append(note)

                # create a datafarame for the QARTOD process
                df = pd.DataFrame(
                {
                    "time": times[:].astype('datetime64[s]'),
                    var_name: values,
                },
                )

                # Get the QARTOD results
                try:
                    results = xyz.apply_qc(df,var_name, config_set)
                    log.info("Generated QC test results for %s", var_name)

                    for testname in results.columns:

                        # create the qartod variable name and get the config specs
                        if testname == 'qartod_rollup_qc':
                            qartodname = 'qartod_'+ var_name + '_primary_flag'
                            # Pass the config specs to a variable
                            testconfig = config_set['contexts'][0]['streams'][var_name]['qartod']
                        else:
                            qartodname = 'qartod_'+ var_name + '_'+ testname.split('qartod_')[-1].split('_test')[0]+'_flag'
                            # Pass the config specs to a variable
                            testconfig = config_set['contexts'][0]['streams'][var_name]['qartod'][testname.split('qartod_')[-1]]

                        # Update the qartod variable
                        log.info("Updating %s", qartodname)
                        qartod_var = ncfile.variables[qartodname]
                        qartod_var[:] = np.array(results[testname].values)
                        qartod_var.qartod_test = f"{testname.split('qartod_')[-1]}"

                        # Set the dictionary as a string attribute to the variable
                        qartod_var.setncattr('qartod_config', json.dumps(testconfig))

                except Exception as e:
                        apply_qc_err = "apply_qc failed: could not calculate QC flags."
                        log.exception(f"{apply_qc_err}: ")
                        report_list.append(f"{apply_qc_err}: {str(e)}")
                        continue
    # log issues qc
    report = ' '.join(report_list).strip()
    ncfile.dac_qc_comment = str(deployment_name) + ' (' + str(file_name) + ': ' + str(report) + ')'

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
    # where file is repeatedly picked are addressed.
    try:
        if os.getxattr(nc_path, "user.qc_run"):
            return False
    except OSError:
        pass
    try:
        with Dataset(nc_path, 'r+') as nc:
            run_qc(config, nc, nc_path)
        os.setxattr(nc_path, "user.qc_run", b"true")
    # set user_qc xattr to error to prevent continuous inotify looping on
    # partially modified netCDF files
    except OSError:
        log.exception(f"Exception occurred trying to save QC to file on {nc_path}:")
        os.setxattr(nc_path, "user.qc_run", b"error")
    except:
        log.exception("Other unhandled error occurred during QC:")
        os.setxattr(nc_path, "user.qc_run", b"error")
    finally:
        lock.release()

def lock_file(path):
    '''
    Acquires a file lock or raises an exception
    :param path string defining path to the netcdf file
    '''
    rc = get_redis_connection()
    key = f"gliderdac:{path}"
    lock = rc.lock(key, blocking_timeout=0)
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

        # TODO: Set time as the extended file attribute
        # Get the current date-time in ISO format
        #iso_date = datetime.datetime.utcnow().isoformat()

        # Convert it to bytes
        #iso_date_bytes = iso_date.encode("utf-8")

        # Set the extended attribute
        #os.setxattr(nc_path, "user.qc_run", iso_date_bytes)

    except OSError:
        log.exception(f"Exception occurred trying to set xattr on already QCed file at {nc_path}:")
    return False
