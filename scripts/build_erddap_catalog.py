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
                f.write(build_erddap_catalog_fragment(data_root, user, deployment, template_dir))

        # if we have an "agg" file in our templates, fill one out per user
        if os.path.exists(os.path.join(template_dir, 'dataset.agg.xml')):
            for user in udeployments:
                f.write(build_erddap_agg_fragment(data_root, user, template_dir))

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

    return template.safe_substitute(dataset_id=deployment,
                                    dataset_dir=dir_path,
                                    institution=institution)

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

    return template.safe_substitute(dataset_id=dataset_id,
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

