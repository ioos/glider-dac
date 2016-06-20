#!/usr/bin/env python
import os
import time
import json
import argparse
import logging
import fileinput
import glob
from jinja2 import Template
from lxml import etree
from collections import defaultdict

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]  %(message)s')
logger = logging.getLogger(__name__)

def build_erddap_catalog(data_root, catalog_root, erddap_name, template_dir, root_dir=None):
    """
    Cats together the head, all fragments, and foot of a datasets.xml
    """
    head_path = os.path.join(template_dir, 'datasets.head.xml')
    tail_path = os.path.join(template_dir, 'datasets.tail.xml')

    # discover all deployments in data directory
    udeployments    = defaultdict(list)
    pattern         = os.path.join(data_root, '*', '*')
    deployment_dirs = glob.glob(pattern)

    for dd in deployment_dirs:
        user, deployment = os.path.split(os.path.relpath(dd, data_root))
        udeployments[user].append(deployment)

    ds_path = os.path.join(catalog_root, erddap_name, 'datasets.xml')
    with open(ds_path, 'w') as f:
        for line in fileinput.input([head_path]):
            f.write(line)

        # for each user deployment, create a dataset fragment
        for user in udeployments:
            for deployment in udeployments[user]:
                f.write(build_erddap_catalog_fragment(data_root, user, deployment, template_dir, root_dir))

        # if we have an "agg" file in our templates, fill one out per user
        if os.path.exists(os.path.join(template_dir, 'dataset.agg.xml')):
            for user in udeployments:
                f.write(build_erddap_agg_fragment(data_root, user, template_dir))

        for line in fileinput.input([tail_path]):
            f.write(line)

    logger.info("Wrote %s from %d deployments", ds_path, len(deployment_dirs))

def build_erddap_catalog_fragment(data_root, user, deployment, template_dir, root_dir=None):
    """
    Builds an ERDDAP dataset xml fragment.
    """
    logger.info("Building ERDDAP catalog fragment for %s/%s", user, deployment)

    # grab template for dataset fragment
    template_path = os.path.join(template_dir, 'dataset.deployment.xml')
    with open(template_path) as f:
        template = Template("".join(f.readlines()))

    # grab institution, if we can find one
    institution     = user
    deployment_name = deployment
    dir_path        = os.path.join(data_root, user, deployment)
    if root_dir:
        deployment_file = os.path.join(root_dir, user, deployment, 'deployment.json')
    else:
        deployment_file = os.path.join(dir_path, "deployment.json")

    try:
        with open(deployment_file) as f:
            js              = json.load(f)
            institution     = js.get('operator', js.get('username'))
            deployment_name = js['name']
            wmo_id          = js.get('wmo_id', '') or ''
            wmo_id          = wmo_id.strip()
            checksum        = js.get('checksum', '').strip()
            completed       = js['completed']
    except (OSError, IOError, AssertionError, AttributeError) as e:
        print "%s: %s" % (repr(e), e.message)
        print e
        return ''

    nc_file = get_first_nc_file(dir_path)
    qartod_variables = []
    if nc_file:
        qartod_variables = check_for_qartod(nc_file)

    return template.render(dataset_id=deployment,
                                    dataset_dir=dir_path,
                                    institution=institution,
                                    checksum=checksum,
                                    completed=completed,
                                    include_qartod=len(qartod_variables)>0,
                                    qartod_variables=qartod_variables)


def get_first_nc_file(root):
    '''
    Returns the first netCDF file found in the directory
    
    :param str root: Root of the directory to scan
    '''
    for content in os.listdir(root):
        if content.endswith('.nc'):
            return os.path.join(root, content)


def check_for_qartod(nc_file):
    from netCDF4 import Dataset
    qartod_variables = []
    with Dataset(nc_file, 'r') as nc:
        for var in nc.variables:
            if var.startswith('qartod_'):
                qartod_variables.append(var)
    return qartod_variables


def build_erddap_agg_fragment(data_root, user, template_dir):
    """
    Builds an aggregate dataset fragment entry.

    For Glider DAC this is on the public ERDDAP instance.
    """
    logger.info("Building ERDDAP catalog aggregation fragment for %s", user)

    # grab template for dataset fragment
    template_path = os.path.join(template_dir, 'dataset.agg.xml')
    with open(template_path) as f:
        template = Template("".join(f.readlines()))

    institution     = user
    dir_path        = os.path.join(data_root, user)

    # grab institution, if we can find from first deployment
    pattern     = os.path.join(data_root, user, "*", "deployment.json")
    deployments = glob.glob(pattern)

    if len(deployments):
        try:
            with open(deployments[0]) as f:
                js              = json.load(f)
                institution     = js.get('operator', js.get('username'))
        except (OSError, IOError, AssertionError, AttributeError):
            pass

    dataset_title   = "All %s Gliders" % institution
    dataset_id      = "all%sGliders" % slugify(institution)

    return template.render(dataset_id=dataset_id,
                                    dataset_dir=dir_path,
                                    dataset_title=dataset_title)

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

def main(mode, data_root, catalog_root, templates, root_dir=None):

    # ensure directories exist
    make_all_dirs(catalog_root, mode)

    if mode == "priv_erddap":
        build_erddap_catalog(data_root, catalog_root, mode, templates, root_dir)
    elif mode == "pub_erddap":
        build_erddap_catalog(data_root, catalog_root, mode, templates, root_dir)
    else:
        raise NotImplementedError("Unknown mode %s" % mode)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['priv_erddap', 'pub_erddap'], help='Which ERDDAP to build the catalog for')
    parser.add_argument('data_dir', help='The directory where netCDF files are read from')
    parser.add_argument('catalog_dir', help='The directory where the datasets.xml will reside')
    parser.add_argument('templates', help='The directory where the XML templates exist')
    parser.add_argument('-r', '--root-dir', help='The directory where the root netCDF files are, and the deployment.json files')

    args      = parser.parse_args()

    catalog   = os.path.realpath(args.catalog_dir)
    data_root = os.path.realpath(args.data_dir)
    templates = os.path.realpath(args.templates)

    root_dir  = None
    if args.root_dir:
        root_dir = os.path.realpath(args.root_dir)


    main(args.mode, data_root, catalog, templates, root_dir)

