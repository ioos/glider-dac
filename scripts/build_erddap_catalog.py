#!/usr/bin/env python
"""
scripts/build_erddap_catalog.py

This script generates dataset "chunks" for gliderDAC deployments and
concatenates them into a single datasets.xml file for ERDDAP. This
script is run on a schedule to help keep the gliderDAC datasets in
sync with newly registered (or deleted) deployments

Details:
Only generates a new dataset chunk if the dataset has been updated since
the last time the script ran. The chunk is saved as dataset.xml in the
deployment directory.

Use the -f CLI argument to create a dataset.xml chunk for ALL the datasets

Optionally add/update metadata to a dataset by supplying a json file named extra_atts.json
to the deployment directory.

An example of extra_atts.json file which modifies the history global
attribute and the depth variable's units attribute is below

{
    "_global_attrs": {
        "history": "updated units"
    },
    "depth": {
        "units": "m"
    }
}
"""

import argparse
import fileinput
import glob
import json
import logging
import numpy as np
import os
import redis
import sys
from collections import defaultdict
from datetime import datetime, timezone
from glider_dac import app, db
from jinja2 import Template
from lxml import etree
from netCDF4 import Dataset
from pathlib import Path
import requests
from sync_erddap_datasets import sync_deployment

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s | %(levelname)s]  %(message)s'
)
logger = logging.getLogger(__name__)


erddap_mapping_dict = defaultdict(lambda: 'String',
                                  { np.int8: 'byte',
                                    np.int16: 'short',
                                    np.float32: 'float',
                                    np.float64: 'double' })

# The directory where the XML templates exist
template_dir = Path(__file__).parent.parent / "glider_dac" / "erddap" / "templates"

# Connect to redis to keep track of the last time this script ran
redis_key = 'build_erddap_catalog_last_run'
redis_host = app.config.get('REDIS_HOST', 'redis')
redis_port = app.config.get('REDIS_PORT', 6379)
redis_db = app.config.get('REDIS_DB', 0)
_redis = redis.Redis(
    host=redis_host,
    port=redis_port,
    db=redis_db
)

def inactive_datasets(deployments_set):
    try:
        resp = requests.get("{}/erddap/tabledap/allDatasets.csv?datasetID".format(app.config["PRIVATE_ERDDAP"]),
                            timeout=10)
        resp.raise_for_status()
        # contents of erddap datasets
        erddap_contents_set = set(resp.text.splitlines()[4:])
    except (requests.Timeout, requests.HTTPError, IndexError):
        erddap_contents_set = set()

    return erddap_contents_set - deployments_set

def build_datasets_xml(data_root, catalog_root, force):
    """
    Cats together the head, all fragments, and foot of a datasets.xml
    """
    head_path = os.path.join(template_dir, 'datasets.head.xml')
    tail_path = os.path.join(template_dir, 'datasets.tail.xml')

    query = {}
    if not force:
        # Get datasets that have been updated since the last time this script ran
        try:
            last_run_ts = _redis.get(redis_key) or 0
            last_run = datetime.utcfromtimestamp(int(last_run_ts))
            query['updated'] = {'$gte': last_run}
        except Exception:
            logger.error("Error: Parsing last run from redis. Processing ALL Datasets")

    # Set the timestamp of this run in redis
    dt_now = datetime.now(tz=timezone.utc)
    _redis.set(redis_key, int(dt_now.timestamp()))

    # First update the chunks of datasets.xml that need updating
    # TODO: Can we use glider_dac_watchdog to trigger the chunk creation?
    deployments = db.Deployment.find(query)
    for deployment in deployments:
        deployment_dir = deployment.deployment_dir
        dataset_chunk_path = os.path.join(data_root, deployment_dir, 'dataset.xml')
        with open(dataset_chunk_path, 'w') as f:
            try:
                f.write(build_erddap_catalog_chunk(data_root, deployment))
            except Exception:
                logger.exception("Error: creating dataset chunk for {}".format(deployment_dir))

    # Now loop through all the deployments and construct datasets.xml
    ds_path = os.path.join(catalog_root, 'datasets.xml')
    deployments_name_set = set()
    deployments = db.Deployment.find()  # All deployments now
    with open(ds_path, 'w') as f:
        for line in fileinput.input([head_path]):
            f.write(line)
        # for each deployment, get the dataset chunk
        for deployment in deployments:
            deployments_name_set.add(deployment.name)
            # First check that a chunk exists
            dataset_chunk_path = os.path.join(data_root, deployment.deployment_dir, 'dataset.xml')
            if os.path.isfile(dataset_chunk_path):
                for line in fileinput.input([dataset_chunk_path]):
                    f.write(line)

        inactive_deployment_names = inactive_datasets(deployments_name_set)

        for inactive_deployment in inactive_deployment_names:
            f.write('\n<dataset type="EDDTableFromNcFiles" datasetID="{}" active="false"></dataset>'.format(
                         inactive_deployment))

        for line in fileinput.input([tail_path]):
            f.write(line)

    logger.info("Wrote {} from {} deployments".format(ds_path, deployments.count()))
    # issue flag refresh to remove inactive deployments after datasets.xml written
    for inactive_deployment_name in inactive_deployment_names:
        sync_deployment(inactive_deployment_name)



def build_erddap_catalog_chunk(data_root, deployment):
    """
    Builds an ERDDAP dataset xml chunk.

    :param str data_root: The root directory where netCDF files are read from
    :param mongo.Deployment deployment: Mongo deployment model
    """
    deployment_dir = deployment.deployment_dir
    logger.info("Building ERDDAP catalog chunk for {}".format(deployment_dir))

    # grab template for dataset fragment
    template_path = os.path.join(template_dir, 'dataset.deployment.xml')
    with open(template_path) as f:
        template = Template("".join(f.readlines()))

    dir_path = os.path.join(data_root, deployment_dir)

    checksum = (deployment.checksum or '').strip()
    completed = deployment.completed
    delayed_mode = deployment.delayed_mode

    # look for a file named extra_atts.json that provides
    # variable and/or global attributes to add and/or modify
    # An example of extra_atts.json file is in the module docstring
    extra_atts = {"_global_attrs": {}}
    extra_atts_file = os.path.join(dir_path, "extra_atts.json")
    if os.path.isfile(extra_atts_file):
        try:
            with open(extra_atts_file) as f:
                extra_atts = json.load(f)
        except Exception:
            logger.error("Error loading file: {}".format(extra_atts_file))

    # Get the latest file from the DB (and double check just in case)
    latest_file = deployment.latest_file or get_latest_nc_file(dir_path)
    if latest_file is None:
        raise IOError('No nc files found in deployment {}'.format(deployment_dir))

    # variables which need to have the variable {var_name}_qc present in the
    # template.  Right now these are all the same, so are hardcoded
    required_qc_vars = {"conductivity_qc", "density_qc", "depth_qc",
                        "latitude_qc", "lat_uv_qc", "longitude_qc",
                        "lon_uv_qc", "profile_lat_qc", "profile_lon_qc",
                        "pressure_qc", "salinity_qc", "temperature_qc",
                        "time_qc", "time_uv_qc", "profile_time_qc",
                        "u_qc", "v_qc"}

    # any destinationNames that need to have a different name.
    # by default the destinationName will equal the sourceName
    dest_var_remaps = {'longitude_qc': 'precise_lon_qc',
                       'latitude_qc': 'precise_lat_qc',
                       'profile_lon_qc': 'longitude_qc',
                       'profile_lat_qc': 'latitude_qc',
                       'time_qc': 'precise_time_qc',
                       'profile_time_qc': 'time_qc'}

    existing_varnames = {'trajectory', 'wmo_id', 'profile_id', 'profile_time',
                         'profile_lat', 'profile_lon', 'time', 'depth',
                         'pressure', 'temperature', 'conductivity', 'salinity',
                         'density', 'lat', 'lon', 'time_uv', 'lat_uv',
                         'lon_uv', 'u', 'v', 'platform', 'instrument_ctd'}

    # need to explicitly cast keys to set in Python 2
    exclude_vars = (existing_varnames | set(dest_var_remaps.keys()) |
                    required_qc_vars | {'latitude', 'longitude'})

    nc_file = os.path.join(data_root, deployment_dir, latest_file)
    with Dataset(nc_file, 'r') as ds:
        qc_var_types = check_for_qc_vars(ds)
        all_other_vars = ds.get_variables_by_attributes(name=lambda n: n not in exclude_vars)
        gts_ingest = getattr(ds, 'gts_ingest', 'true')  # Set default value to true
        templ = template.render(
            dataset_id=deployment.name,
            dataset_dir=dir_path,
            checksum=checksum,
            completed=completed,
            reqd_qc_vars=required_qc_vars,
            dest_var_remaps=dest_var_remaps,
            qc_var_types=qc_var_types,
            gts_ingest=gts_ingest,
            delayed_mode=delayed_mode
        )
        # Add any of the extra variables and attributes
        try:
            tree = etree.fromstring(templ)
            for identifier, mod_attrs in extra_atts.items():
                add_extra_attributes(tree, identifier, mod_attrs)
            # append all the 'other' variables to etree
            for var in all_other_vars:
                tree.append(add_erddap_var_elem(var))
            return etree.tostring(tree, encoding=str)
        except Exception:
            logger.exception("Exception occurred while adding atts to template: {}".format(deployment_dir))
            return templ


def add_erddap_var_elem(var):
    """
    Adds an unhandled standard name variable to the ERDDAP datasets.xml
    """
    dvar_elem = etree.Element('dataVariable')
    source_name = etree.SubElement(dvar_elem, 'sourceName')
    source_name.text = var.name
    data_type = etree.SubElement(dvar_elem, 'dataType')
    data_type.text = erddap_mapping_dict[var.dtype.type]
    add_atts = etree.SubElement(dvar_elem, 'addAttributes')
    ioos_category = etree.SubElement(add_atts, 'att', name='ioos_category')
    ioos_category.text = "Other"
    return dvar_elem


def add_extra_attributes(tree, identifier, mod_atts):
    """
    Adds extra user-defined attributes to the ERDDAP datasets.xml.
    Usually sourced from the extra_atts.json file, this function modifies an
    ERDDAP xml datasets tree.   `identifier` should either be "_global_attrs"
    to modify a global attribute, or the name of a variable in the dataset
    to modify a variable's attributes.  `mod_atts` is a dict with the attributes
    to create or modify.
    """
    if identifier == '_global_attrs':
        xpath_expr = "."
    else:
        xpath_expr = "dataVariable[sourceName='{}']".format(identifier)
    subtree = tree.find(xpath_expr)

    if subtree is None:
        logger.warning("Element specified By XPath expression {} not found, skipping".format(xpath_expr))
        return

    add_atts_found = subtree.find('addAttributes')
    if add_atts_found is not None:
        add_atts_elem = add_atts_found
    else:
        add_atts_elem = subtree.append(etree.Element('addAttributes'))
        logger.info('Added "addAttributes" to xpath for {}'.format(xpath_expr))

    for att_name, value in mod_atts.items():
        # find the attribute
        found_elem = add_atts_elem.find(att_name)
        # attribute exists, update current value
        if found_elem is not None:
            found_elem.text = value
        # attribute
        else:
            new_elem = etree.Element('att', {'name': att_name})
            new_elem.text = value
            add_atts_elem.append(new_elem)


def check_for_qc_vars(nc):
    """
    Checks for general gc variables and QARTOD variables by naming conventions.
    Returns a dict with both sets of variables as keys, and their attributes
    as values.
    """
    qc_vars = {'gen_qc': {}, 'qartod': {}}
    for var in nc.variables:
        if var.endswith('_qc'):
            qc_vars['gen_qc'][var] = nc.variables[var].ncattrs()
        elif var.startswith('qartod'):
            qc_vars['qartod'][var] = nc.variables[var].ncattrs()
    return qc_vars


def get_latest_nc_file(root):
    '''
    Returns the lastest netCDF file found in the directory

    :param str root: Root of the directory to scan
    '''
    list_of_files = glob.glob('{}/*.nc'.format(root))
    if not list_of_files:  # Check for no files
        return None
    return max(list_of_files, key=os.path.getctime)


def main(data_dir, catalog_dir, force):
    '''
    Entrypoint for build ERDDAP catalog script.
    '''
    # ensure datasets.xml directory exists
    os.makedirs(catalog_dir, exist_ok=True)
    build_datasets_xml(data_dir, catalog_dir, force)


if __name__ == "__main__":
    '''
    build_erddap_catalog.py priv_erddap ./data/data/priv_erddap ./data/catalog ./glider_dac/erddap/templates/private
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('data_dir', help='The directory where netCDF files are read from')
    parser.add_argument('catalog_dir', help='The full path to where the datasets.xml will reside')
    parser.add_argument('-f', '--force', action="store_true", help="Force processing ALL deployments")

    args = parser.parse_args()

    catalog_dir = os.path.realpath(args.catalog_dir)
    data_dir = os.path.realpath(args.data_dir)
    force = args.force

    with app.app_context():
        sys.exit(main(data_dir, catalog_dir, force))
