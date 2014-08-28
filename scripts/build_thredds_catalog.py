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
    head_path = os.path.join(template_dir, 'catalog.head.xml')
    tail_path = os.path.join(template_dir, 'catalog.tail.xml')

    # discover all deployments in data directory
    udeployments    = defaultdict(list)
    pattern         = os.path.join(data_root, '*', '*')
    deployments = glob.glob(pattern)

    for dd in deployments:
        user, deployment = os.path.split(os.path.relpath(dd, data_root))
        udeployments[user].append(deployment)

    catalog_path = os.path.join(catalog_root, 'thredds', 'catalog.xml')
    with open(catalog_path, 'w') as f:
        for line in fileinput.input([head_path]):
            f.write(line)

        # for each deployment file create a fragment
        for user in udeployments:
            for deployment in udeployments[user]:
                f.write(build_thredds_catalog_fragment(data_root, user, deployment, template_dir))

        # @TODO: aggregations?

        for line in fileinput.input([tail_path]):
            f.write(line)

    logger.info("Wrote %s from %d deployments", catalog_path, len(deployments))

def build_thredds_catalog_fragment(data_root, user, deployment, template_dir):
    """
    Builds a thredds catalog entry
    """
    logger.info("Building THREDDS catalog fragment for %s/%s", user, deployment)

    # grab template for dataset fragment
    template_path = os.path.join(template_dir, 'catalog.deployment.xml')
    with open(template_path) as f:
        template = Template("".join(f.readlines()))

    user            = user
    deployment      = deployment
    deployment_file = "%s.nc3.nc" % deployment
    dataset_id      = slugify("%s_%s" % (user, deployment))
    deployment_path = os.path.join(data_root, user, deployment, deployment_file)

    return template.safe_substitute(user=user,
                                    deployment=deployment,
                                    deployment_file=deployment_file,
                                    dataset_id=dataset_id,
                                    deployment_path=deployment_path)

def _create_ncml(user, deployment):

    dir_path = os.path.join(base, user, deployment)
    cat_path = os.path.join(catalog, 'thredds', user, deployment)

    try:
        os.makedirs(cat_path)
    except OSError:
        # Dir Already exists
        pass

    # Add WMO ID if it exists
    try:
      with open(os.path.join(dir_path, "deployment.json")) as f:
        js     = json.load(f)
        wmo_id = js['wmo_id'].strip()
        assert len(wmo_id) > 0
    except (IOError, AssertionError, AttributeError):
      # No wmoid.txt file
      wmo_id = "NotAssigned"

    time_agg = """<?xml version="1.0" encoding="UTF-8"?>
        <netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">
          <remove type="variable" name="time_uv"/>
          <remove type="variable" name="lat_uv"/>
          <remove type="variable" name="lon_uv"/>
          <remove type="variable" name="u"/>
          <remove type="variable" name="u_qc"/>
          <remove type="variable" name="v_qc"/>

          <variable name="platform">
            <attribute name="wmo_id" value="%(wmo_id)s" />
          </variable>

          <aggregation dimName="time" type="joinExisting" recheckEvery="5 min">
            <scan location="%(dir_path)s" suffix=".nc" subdirs="false" />
          </aggregation>
        </netcdf>
        """ % locals()

    with open(os.path.join(cat_path, "timeagg.ncml"), 'w') as f:
        f.write(time_agg)


    time_uv_agg = """<?xml version="1.0" encoding="UTF-8"?>
        <netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">
          <remove type="variable" name="time"/>
          <remove type="variable" name="time_qc"/>
          <remove type="variable" name="segment_id"/>
          <remove type="variable" name="profile_id"/>
          <remove type="variable" name="depth"/>
          <remove type="variable" name="depth_qc"/>
          <remove type="variable" name="lat"/>
          <remove type="variable" name="lat_qc"/>
          <remove type="variable" name="lon"/>
          <remove type="variable" name="lon_qc"/>
          <remove type="variable" name="pressure"/>
          <remove type="variable" name="pressure_qc"/>
          <remove type="variable" name="conductivity"/>
          <remove type="variable" name="conductivity_qc"/>
          <remove type="variable" name="density"/>
          <remove type="variable" name="density_qc"/>
          <remove type="variable" name="salinity"/>
          <remove type="variable" name="salinity_qc"/>
          <remove type="variable" name="temperature"/>
          <remove type="variable" name="temperature_qc"/>

          <variable name="platform">
            <attribute name="wmo_id" value="%(wmo_id)s" />
          </variable>

          <aggregation dimName="time_uv" type="joinExisting" recheckEvery="5 min">
            <scan location="%(dir_path)s" suffix=".nc" subdirs="false" />
          </aggregation>
        </netcdf>
        """ % locals()

    with open(os.path.join(cat_path, "timeuvagg.ncml"), 'w') as f:
        f.write(time_uv_agg)

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
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip())
    return unicode(re.sub('[-\s]+', '-', value))

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

