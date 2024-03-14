#!/usr/bin/env python
'''
tests/test_glider_qc.py
'''

from glider_qc.glider_qc import GliderQC
from unittest import TestCase
from netCDF4 import Dataset
from tests.resources import STATIC_FILES
import yaml
import tempfile
import os
import numpy as np
import numpy.ma as ma


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

        results_raw = qc.apply_qc(STATIC_FILES['murphy'], 'temperature', qc_config)

        results_dict = {r.test: r.results for r in results_raw if r.stream_id == 'temperature'}
        np.testing.assert_equal(
            np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.int8),
            results_dict['gross_range_test'])

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
        timevar[np.array([0, 2, 4, 6, 8])] = np.array([0, 2, 4, 6, 8])
        tempvar = nc.createVariable('temp', np.float32, ('time',), fill_value=-9999.)
        tempvar.standard_name = 'sea_water_temperature'
        tempvar.units = 'deg_F'
        tempvar[np.array([0, 1, 2, 3, 4, 9])] = np.array([72.0, 72.1, 72.0, 1.0, 72.03, 72.1])

        qc = GliderQC(fake_file, 'data/qc_config.yml')
        with open('data/qc_config.yml') as yaml_content:
            qc_config = yaml.safe_load(yaml_content)
        qc_config["contexts"][0]["streams"]["temp"] = qc_config["contexts"][0]["streams"]["temperature"]
        del qc_config["contexts"][0]["streams"]["temperature"]

        results_raw = qc.apply_qc(fake_file, 'temp', qc_config)

        results_dict = {r.test: r.results for r in results_raw if r.stream_id == 'temp'}

        np.testing.assert_equal(results_dict['flat_line_test'][:].mask, ~np.array([1, 0, 1, 0, 1, 0, 0, 0, 0, 0], dtype=bool))
        np.testing.assert_equal(results_dict['flat_line_test'][:], np.array([1, 9, 1, 9, 1, 9, 9, 9, 9, 9], dtype=np.int8))

    def test_normalize_variable(self):
        values = np.array([32.0, 65.0, 100.0])
        units = 'deg_F'
        standard_name = 'sea_water_temperature'

        converted = GliderQC.normalize_variable(values, units, standard_name)
        np.testing.assert_almost_equal(np.array([0, 18.3333, 37.777778]), converted, 2)
