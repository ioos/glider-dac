#!/usr/bin/env python
'''
tests/test_glider_qc.py
'''

from unittest import TestCase
from netCDF4 import Dataset
import yaml
import tempfile
import os
import numpy as np
import numpy.ma as ma
import pandas as pd
from glider_qc.glider_qc import GliderQC
from tests.resources import STATIC_FILES


class TestGliderQC(TestCase):

    def copy_ncfile(self, ncpath):
        fd, path = tempfile.mkstemp()
        self.addCleanup(os.remove, path)
        with open(ncpath, 'rb') as f:
            buf = f.read()
        os.write(fd, buf)
        os.close(fd)
        return path

    def test_find_geophysical_varaibles(self):
        ncfile = Dataset(STATIC_FILES['murphy'], 'r')
        self.addCleanup(ncfile.close)

        qc = GliderQC(ncfile, 'data/qc_config.yml')
        variables = qc.find_geophysical_variables()[0]
        assert len(variables) == 5
        assert 'temperature' in variables
        assert 'salinity' in variables
        assert 'pressure' in variables

    def test_create_qc_variables(self):
        copypath = self.copy_ncfile(STATIC_FILES['murphy'])
        ncfile = Dataset(copypath, 'r+')
        self.addCleanup(ncfile.close)

        qc = GliderQC(ncfile, 'data/qc_config.yml')
        temperature = ncfile.variables['temperature']
        qc.create_qc_variables(temperature)

        expected = [
            'qartod_temperature_flat_line_flag',
            'qartod_temperature_gross_range_flag',
            'qartod_temperature_rate_of_change_flag',
            'qartod_temperature_spike_flag'
        ]
        for name in expected:
            assert name in ncfile.variables

        ancillary_variables = temperature.ancillary_variables
        assert 'qartod_temperature_spike_flag' in ancillary_variables

    def test_apply_qc(self):
        copypath = self.copy_ncfile(STATIC_FILES['murphy'])
        ncfile = Dataset(copypath, 'r+')
        self.addCleanup(ncfile.close)

        qc = GliderQC(ncfile, 'data/qc_config.yml')
        with open('data/qc_config.yml') as yaml_content:
            qc_config = yaml.safe_load(yaml_content)

        times = ncfile.variables['time']
        values = ncfile.variables['temperature']
        values = [x if x != '--' else np.nan for x in values[:]]
        values, note = qc.normalize_variable(np.array(values[:]),
                                             ncfile.variables['temperature'].units,
                                             ncfile.variables['temperature'].standard_name)

        df = pd.DataFrame({"time": times[:].astype('datetime64[s]'), "temperature": values,},)

        results_raw = qc.apply_qc(df, 'temperature', qc_config, ncfile_path=None)

        np.testing.assert_equal(
            np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.int8),
            np.array(results_raw['temperature_qartod_gross_range_test'].values))

        np.testing.assert_equal(
            np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.int8),
            np.array(results_raw['temperature_qartod_flat_line_test'].values))

        np.testing.assert_equal(
            np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.int8),
            np.array(results_raw['temperature_qartod_rate_of_change_test'].values))

        np.testing.assert_equal(
            np.array([2, 1, 1, 1, 1, 1, 1, 2], dtype=np.int8),
            np.array(results_raw['temperature_qartod_spike_test'].values))

    def test_units_qc(self):
        fd, fake_file = tempfile.mkstemp()
        os.close(fd)
        self.addCleanup(os.remove, fake_file)

        nc = Dataset(fake_file, 'w')
        nc.createDimension('time', 10)
        timevar = nc.createVariable('time', np.float64, ('time',), fill_value=-9999.)
        timevar.standard_name = 'time'
        timevar.units = 'seconds since 1970-01-01T00:00:00Z'

        # Create datetime64 array
        dt_array = np.arange(
            "2015-01-01T00:00:00",
            "2015-01-01T03:30:00",
            step=np.timedelta64(21, "m"),
            dtype='datetime64[m]'
        )
        # Convert to seconds since epoch
        epoch = np.datetime64("1970-01-01T00:00:00", "s")
        seconds_since_epoch = (dt_array.astype('datetime64[s]') - epoch).astype(float)
        timevar[:] = seconds_since_epoch

        tempvar = nc.createVariable('temp', np.float32, ('time',), fill_value=-9999.)
        tempvar.standard_name = 'sea_water_temperature'
        tempvar.units = 'deg_F'
        tempvar[np.array([0, 1, 2, 3, 4, 6, 7, 8])] = np.array([71, 72, 72.0001, 72, 72.0001, 72.0001, 72, 74])

        qc = GliderQC(fake_file, 'data/qc_config.yml')
        with open('data/qc_config.yml') as yaml_content:
            qc_config = yaml.safe_load(yaml_content)
        qc_config["contexts"][0]["streams"]["temp"] = qc_config["contexts"][0]["streams"]["temperature"]
        del qc_config["contexts"][0]["streams"]["temperature"]

        times = nc.variables['time']
        values = nc.variables['temp']
        values = [x if x != '--' else np.nan for x in values[:]]
        values, note = qc.normalize_variable(np.array(values[:]), tempvar.units, tempvar.standard_name)

        df = pd.DataFrame({"time": times[:].astype('datetime64[s]'), "temp": values,},)
        results_raw = qc.apply_qc(df, 'temp', qc_config, ncfile_path=None)

        np.testing.assert_equal(np.array(results_raw['temp_qartod_flat_line_test'].values), np.array([1, 1, 1, 3, 4, 9, 4, 4, 1, 9], dtype=np.int8))

    def test_normalize_variable(self):
        values = np.array([32.0, 65.0, 100.0])
        units = 'deg_F'
        standard_name = 'sea_water_temperature'

        converted, note = GliderQC.normalize_variable(values, units, standard_name)
        np.testing.assert_almost_equal(np.array([0, 18.3333, 37.777778]), converted, 2)


    def make_time_array(self, start_dt, count=10, step_sec=60):
        '''
            Create a numpy masked array of datetime64[s] starting at start_dt, with count total timestamps, and step_sec seconds between them.
        '''
        # Create a numpy masked array of datetime64[s] starting at start_dt
        times = np.array([np.datetime64(start_dt + i * step_sec, 's') for i in range(count)])
        return ma.array(times)

    def create_temp_nc(self, deployment_name):
        '''
            Create a temporary NetCDF file with a dummy variable and return its path.
            The returned path is formatted as if the file were in the deployment_name directory.
        '''
        # Create a temporary NetCDF file with a dummy variable
        tempdir = tempfile.mkdtemp()
        nc_path = os.path.join(tempdir, 'file.nc')
        ncfile = Dataset(nc_path, 'w', format='NETCDF4')
        ncfile.createDimension('time', 10)
        ncfile.createVariable('temperature', 'f4', ('time',))
        ncfile.close()
        # Return path as if it were in the deployment_name directory
        return os.path.join(tempdir, 'file.nc'), f"{tempdir}/{deployment_name}/file.nc"

    def test_time_format_base_case(self):
        '''
            Test that a deployment name with a valid timestamp is accepted.
            MISSING MONTH or DAY (QC result should not include "deployment name missing valid timestamp: " + deployment_name)
            INVALID YEAR (QC result should not include "Deployment time missing or invalid: Year XXXX is greater than maximum allowed year_now.")
        '''
        # deployment_name = 'unitglider-20230515T120000'
        deployment_name = 'unitglider-20230515T_extra'
        nc_file, nc_path = self.create_temp_nc(deployment_name)
        tnp = self.make_time_array(np.datetime64('2023-05-15T12:00:00', 's'))
        ncfile = Dataset(nc_file, 'r+')
        self.addCleanup(ncfile.close)
        qc = GliderQC(ncfile, 'data/qc_config.yml')
        result = qc.check_time(tnp, nc_path)
        assert result == ''

    def test_time_format_masked(self):
        '''
        test if timestamps are masked, the QC should report "masked timestamps" and not proceed to check the deployment name timestamp format.
        if not masked, the QC should check the deployment name timestamp format and report if it's accepted.
        '''
        deployment_name = 'unitglider-30230515T120000'
        nc_file, nc_path = self.create_temp_nc(deployment_name)
        # Make all timestamps unique except the masked one
        times = [np.datetime64('2023-05-15T12:00:00', 's') + np.timedelta64(i, 'm') for i in range(10)]
        mask = [True] + [False]*9
        tnp = ma.array(times, mask=mask)
        ncfile = Dataset(nc_file, 'r+')
        self.addCleanup(ncfile.close)
        qc = GliderQC(ncfile, 'data/qc_config.yml')
        result = qc.check_time(tnp, nc_path)
        assert 'masked timestamps' in result

    def test_time_format_non_ascending(self):
        '''
        test if timestamps are not in ascending order, the QC should report "timestamps out of order" and not proceed to (1) check the deployment name timestamp format or
        (2) check if start time precedes deployment time.
        if timestamps are in ascending order and the deployment time precedes the start time, the QC should check the deployment name timestamp format and report if it's accepted.
        '''
        deployment_name = 'unitglider-20230515T120000'
        nc_file, nc_path = self.create_temp_nc(deployment_name)
        # All unique, but not in order

        # np.datetime64('2023-05-15T11:59:00', 's'),
        times = [

            np.datetime64('2023-05-15T12:00:00', 's'),
            np.datetime64('2023-05-15T12:01:00', 's'),
            np.datetime64('2023-05-15T12:02:00', 's'),
            np.datetime64('2023-05-15T12:03:00', 's'),
            np.datetime64('2023-05-15T12:04:00', 's'),
            np.datetime64('2023-05-15T12:06:00', 's'),
            np.datetime64('2023-05-15T12:07:00', 's'),
            np.datetime64('2023-05-15T12:08:00', 's'),
            np.datetime64('2023-05-15T12:05:00', 's'),
        ]
        tnp = ma.array(times)
        ncfile = Dataset(nc_file, 'r+')
        self.addCleanup(ncfile.close)
        qc = GliderQC(ncfile, 'data/qc_config.yml')
        result = qc.check_time(tnp, nc_path)

        assert 'timestamps out of order' in result

    def test_time_format_duplicate(self):
        '''
        test if timestamps contain duplicates. The QC should report "duplicate timestamps" and not proceed to check the deployment name timestamp format.
        If no duplicates in the results, the QC should check the deployment name timestamp format and report any errors in the results.
        '''
        deployment_name = 'unitglider-20230515T120000'
        nc_file, nc_path = self.create_temp_nc(deployment_name)

        # test no duplicate example
        times = [np.datetime64('2023-05-15T12:00:00', 's')] * 10

        # test duplicate example
        #times = [np.datetime64('2023-05-15T12:00:00', 's') + np.timedelta64(i, 'm') for i in range(10)]

        tnp = ma.array(times)
        ncfile = Dataset(nc_file, 'r+')
        self.addCleanup(ncfile.close)
        qc = GliderQC(ncfile, 'data/qc_config.yml')
        result = qc.check_time(tnp, nc_path)
        print(f"QC result: {result!r}")
        assert 'duplicate timestamps' in result
