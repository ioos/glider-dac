from netCDF4 import Dataset
from unittest import TestCase
from pathlib import Path
import os
from tests.resources import STATIC_FILES
from bson import ObjectId
from datetime import datetime
from scripts.build_erddap_catalog import build_erddap_catalog_chunk
from lxml import etree

# this is used as a helper class to mock Mongo models, as they use attribute-
# based field access, rather than dict keys
class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class TestGliderXml(TestCase):

    def setUp(self):
        # generate dataset from cdl as side effect if not already present
        STATIC_FILES["murphy"]
        self.directory = os.path.dirname(__file__)
        # TODO: treat like DB fixture if we decide to change ORMs at some point
        self.deployment = DotDict({
             '_id': ObjectId('000000000000000000000000'),
             'username': 'test',
             'updated': datetime.now(),
             'estimated_deploy_location': None, 'user_id':
              ObjectId('111111111111111111111111'),
             'name': 'Murphy-20150809T135508Z_rt.nc',
             'archive_safe': True,
             'created': datetime.now(),
             'compliance_check_passed': False,
             'checksum': '22222222222222222222222222222222',
             'completed': True, 'deployment_date': datetime.now(),
             'deployment_dir': 'data/Murphy-20150809T135508Z_rt',
             'glider_name': 'Murphy', 'wmo_id': '4801904',
             'operator': '', 'attribution': None, 'estimated_deploy_date': None,
             'delayed_mode': None,
             'latest_file': 'Murphy-20150809T135508Z_rt.nc',
             'latest_file_mtime': datetime(2017, 2, 7, 20, 35, 23)})

    def xpath_var_helper_name(self, xml_tree):
        names = []
        for variable in xml_tree.findall("dataVariable"):
            # Some variables have a sourceName but no destinationName.
            # Favor the latter, but fall back to the former if not present.

            dest_name = variable.find("destinationName")
            if dest_name is not None:
                names.append(dest_name.text)
            else:
                names.append(variable.find("sourceName").text)

        return names

    def test_check_variable_order(self):
        """
        Check that the XML snippets generated have core variables first,
        followed by the remaining variables in an alphabetical fashion. Also
        check that no duplicate variable names are present in the outputted
        XML snippet.
        """
        xml_string = build_erddap_catalog_chunk(self.directory, self.deployment)
        xml_tree = etree.fromstring(xml_string)
        variable_names = self.xpath_var_helper_name(xml_tree)
        # check that core variables always come first
        expected_core_variables = ["trajectory", "wmo_id",
                                   "profile_id", "time", "latitude",
                                   "longitude", "depth"]
        assert (variable_names[:len(expected_core_variables)] ==
                expected_core_variables)
        # for variables which come after core variables, they should be
        # alphabetized
        lowercased_vars = [var.lower() for var in
                           variable_names[len(expected_core_variables):]]
        assert sorted(lowercased_vars) == lowercased_vars
        # Check that no variable names are duplicated, as this will cause
        # ERDDAP not to load a dataset
        assert len(variable_names) == len(set(variable_names))
