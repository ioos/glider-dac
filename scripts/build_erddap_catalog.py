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

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]  %(message)s')
logger = logging.getLogger(__name__)

RSYNC_TO_PATH         = os.environ.get("RSYNC_TO_PATH")
CATALOG_ROOT          = os.environ.get("CATALOG_ROOT")
DATA_ROOT             = os.environ.get("DATA_ROOT")
PRIV_ERDDAP_TEMPLATES = os.environ.get("PRIV_ERDDAP_TEMPLATES")
PUB_ERDDAP_TEMPLATES  = os.environ.get("PUB_ERDDAP_TEMPLATES")

def build_erddap_catalog(data_root, catalog_root, erddap_name, template_dir):
    """
    Cats together the head, all fragments, and foot of a datasets.xml
    """
    head_path = os.path.join(template_dir, 'datasets.head.xml')
    tail_path = os.path.join(template_dir, 'datasets.tail.xml')

    # discover all deployments in data directory
    pattern = os.path.join(data_root, '*', '*')
    deployment_dirs = glob.glob(pattern)

    ds_path = os.path.join(catalog_root, erddap_name, 'datasets.xml')
    with open(ds_path, 'w') as f:
        for line in fileinput.input([head_path]):
            f.write(line)

        for dd in deployment_dirs:
            user, deployment = os.path.split(os.path.relpath(dd, data_root))
            f.write(build_erddap_catalog_fragment(data_root, user, deployment, template_dir))

        for line in fileinput.input([tail_path]):
            f.write(line)

    logger.info("Wrote %s from %d deployments", ds_path, len(deployment_dirs))

def build_erddap_catalog_fragment(data_root, user, deployment, template_dir):
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
    try:
        with open(os.path.join(dir_path, "deployment.json")) as f:
            js              = json.load(f)
            institution     = js.get('operator', js.get('username'))
            deployment_name = js['name']
            wmo_id          = js['wmo_id'].strip()
    except (OSError, IOError, AssertionError, AttributeError):
        pass

    return template.substitute(dataset_id=deployment,
                               dataset_dir=dir_path,
                               institution=institution)

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

def main(mode, data_root, catalog_root, templates):

    # ensure directories exist
    make_all_dirs(catalog_root, mode)

    if mode == "priv_erddap":
        build_erddap_catalog(data_root, catalog_root, mode, templates)
    elif mode == "pub_erddap":
        build_erddap_catalog(data_root, catalog_root, mode, templates)
    else:
        raise NotImplementedError("Unknown mode %s" % mode)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('mode',
                        choices=['priv_erddap', 'pub_erddap', 'thredds'])
    parser.add_argument('data_dir',
                        default=DATA_ROOT)
    parser.add_argument('catalog_dir',
                        default=CATALOG_ROOT)
    parser.add_argument('templates',
                        nargs='?')

    args      = parser.parse_args()

    catalog   = os.path.realpath(args.catalog_dir)
    data_root = os.path.realpath(args.data_dir)
    templates = os.path.realpath(args.templates)

    main(args.mode, data_root, catalog, templates)

