#!/usr/bin/env python
import os
import time
import json
import argparse
import logging
import fileinput
import glob
from string import Template
from lxml import etree
from collections import defaultdict

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]  %(message)s')
logger = logging.getLogger(__name__)

def build_thredds_catalog(data_root, catalog_root, template_dir):
    """
    Creates THREDDS catalog files for the given user/deployment.
    """
    raise NotImplementedError("build_thredds_catalog has been removed in "
                              "favor of utilizing a THREDDS datasetScan, "
                              "see glider_dac/thredds/templates/catalog.xml")


def build_thredds_catalog_fragment(data_root, user, deployment, template_dir):
    """
    Builds a thredds catalog entry
    """
    raise NotImplementedError("build_thredds_catalog fragment has been removed "
                              "in favor of utilizing a THREDDS datasetScan, "
                              "see glider_dac/thredds/templates/catalog.xml")
def make_all_dirs(catalog_root, mode):
    """
    Ensures directory creation for a catalog.
    """
    d = os.path.join(catalog_root, mode)

    if not os.path.exists(d):
        logger.info("Creating %s", d)
        try:
            os.makedirs(d)
        except OSError:
            pass

def slugify(value):
    """
    Normalizes string, removes non-alpha characters, and converts spaces to hyphens.
    Pulled from Django
    """
    import unicodedata
    import re
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = str(re.sub('[^\w\s-]', '', value).strip())
    return str(re.sub('[-\s]+', '-', value))

def main(data_root, catalog_root, templates):

    # ensure directories exist
    make_all_dirs(catalog_root, 'thredds')
    build_thredds_catalog(data_root, catalog_root, templates)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir')
    parser.add_argument('catalog_dir')
    parser.add_argument('templates', nargs='?')

    args      = parser.parse_args()

    catalog   = os.path.realpath(args.catalog_dir)
    data_root = os.path.realpath(args.data_dir)
    templates = os.path.realpath(args.templates)

    main(data_root, catalog, templates)

