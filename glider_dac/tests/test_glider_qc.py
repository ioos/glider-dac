#!/usr/bin/env python
'''
tests/test_glider_qc.py
'''

from glider_qc.glider_qc import GliderQC
from unittest import TestCase
from netCDF4 import Dataset
import glider_dac
from glider_dac.tests.resources import STATIC_FILES
import yaml
import tempfile
import os
import numpy as np
import numpy.ma as ma
import pandas as pd


class TestGliderQC(TestCase):

    qc_conf_loc = os.path.join(os.path.dirname(glider_dac.__file__), 'data/qc_config.yml')

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

        qc = GliderQC(ncfile, self.qc_conf_loc)
        variables = qc.find_geophysical_variables()[0]
        assert len(variables) == 5
        assert 'temperature' in variables
        assert 'salinity' in variables
        assert 'pressure' in variables

    def test_create_qc_variables(self):
        copypath = self.copy_ncfile(STATIC_FILES['murphy'])
        ncfile = Dataset(copypath, 'r+')
        self.addCleanup(ncfile.close)

        qc = GliderQC(ncfile, self.qc_conf_loc)
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

        qc = GliderQC(ncfile, self.qc_conf_loc)
        with open(self.qc_conf_loc) as yaml_content:
            qc_config = yaml.safe_load(yaml_content)

        times = ncfile.variables['time']
        values = ncfile.variables['temperature']
        values = [x if x != '--' else np.nan for x in values[:]]
        values, note = qc.normalize_variable(np.array(values[:]),
                                             ncfile.variables['temperature'].units,
                                             ncfile.variables['temperature'].standard_name)

        df = pd.DataFrame({"time": times[:].astype('datetime64[s]'), "temperature": values,},)

        results_raw = qc.apply_qc(df, 'temperature', qc_config)

        results_dict = {r.test: r.results for r in results_raw if r.stream_id == 'temperature'}

        np.testing.assert_equal(
            np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.int8),
            results_dict['gross_range_test'][:])

        np.testing.assert_equal(
            np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.int8),
            results_dict['flat_line_test'])

        np.testing.assert_equal(
            np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.int8),
            results_dict['rate_of_change_test'])

        np.testing.assert_equal(
            np.array([2, 1, 1, 1, 1, 1, 1, 2], dtype=np.int8),
            results_dict['spike_test'])

    def test_units_qc(self):
        fd, fake_file = tempfile.mkstemp()
        os.close(fd)
        self.addCleanup(os.remove, fake_file)

        nc = Dataset(fake_file, 'w')
        nc.createDimension('time', 10)
        timevar = nc.createVariable('time', np.float64, ('time',), fill_value=-9999.)
        timevar.standard_name = 'time'
        timevar.units = 'seconds since 1970-01-01T00:00:00Z'
        timevar[np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])] =  np.array(np.arange(
                                                                                "2015-01-01 00:00:00",
                                                                                "2015-01-01 03:30:00",
                                                                                step=np.timedelta64(21, "m"),
                                                                                dtype=np.datetime64,
                                                                            ))
        tempvar = nc.createVariable('temp', np.float32, ('time',), fill_value=-9999.)
        tempvar.standard_name = 'sea_water_temperature'
        tempvar.units = 'deg_F'
        tempvar[np.array([0, 1, 2, 3, 4, 6, 7, 8])] = np.array([71, 72, 72.0001, 72, 72.0001, 72.0001, 72, 74])

        qc = GliderQC(fake_file, self.qc_conf_loc)
        with open(self.qc_conf_loc) as yaml_content:
            qc_config = yaml.safe_load(yaml_content)
        qc_config["contexts"][0]["streams"]["temp"] = qc_config["contexts"][0]["streams"]["temperature"]
        del qc_config["contexts"][0]["streams"]["temperature"]

        times = nc.variables['time']
        values = nc.variables['temp']
        values = [x if x != '--' else np.nan for x in values[:]]
        values, note = qc.normalize_variable(np.array(values[:]), tempvar.units, tempvar.standard_name)

        df = pd.DataFrame({"time": times[:].astype('datetime64[s]'), "temp": values,},)
        results_raw = qc.apply_qc(df, 'temp', qc_config)

        results_dict = {r.test: r.results for r in results_raw if r.stream_id == 'temp'}

        np.testing.assert_equal(results_dict['flat_line_test'][:], np.array([1, 1, 1, 3, 4, 9, 4, 4, 1, 9], dtype=np.int8))

    def test_normalize_variable(self):
        values = np.array([32.0, 65.0, 100.0])
        units = 'deg_F'
        standard_name = 'sea_water_temperature'

        converted, note = GliderQC.normalize_variable(values, units, standard_name)
        np.testing.assert_almost_equal(np.array([0, 18.3333, 37.777778]), converted, 2)
