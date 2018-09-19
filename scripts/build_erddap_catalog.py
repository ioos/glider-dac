#!/usr/bin/env python
import os
import time
import json
import argparse
import logging
import fileinput
import glob
import warnings
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
                try:
                    f.write(build_erddap_catalog_fragment(data_root, user,
                                                          deployment, template_dir,
                                                          root_dir, erddap_name))
                except Exception as e:
                    warnings.warn("Error: deployment: {}, user: {}\n{}".format(deployment, user, str(e)))
        # if we have an "agg" file in our templates, fill one out per user
        if os.path.exists(os.path.join(template_dir, 'dataset.agg.xml')):
            for user in udeployments:
                try:
                    f.write(build_erddap_agg_fragment(data_root, user, template_dir))
                except Exception as e:
                    warnings.warn("Error: user: {}\n{}".format(user, str(e)))

        for line in fileinput.input([tail_path]):
            f.write(line)

    logger.info("Wrote %s from %d deployments", ds_path, len(deployment_dirs))

def build_erddap_catalog_fragment(data_root, user, deployment, template_dir,
                                  root_dir=None, mode='pub_erddap'):
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
        print("%s: %s" % (repr(e), e.message))
        print(e)
        return ''


    # look for a file named extra_atts.json that provides
    # variable and/or global attributes to add and/or modify
    # an example of extra_atts.json file which modifies the history global
    # attribute and the depth variable's units attribute is below
    #
    #  {
    #      "_global_attrs":
    #      { "history": "updated units"},
    #      "depth":
    #         { "units": "m" }
    #  }
    extra_atts_file = os.path.join(dir_path, "extra_atts.json")
    if mode == 'priv_erddap' and os.path.isfile(extra_atts_file):
        try:
            with open(extra_atts_file) as f:
                extra_atts = json.load(f)
        except:
            logger.exception("Error loading extra_atts.json file:")
            extra_atts = {}
    else:
        extra_atts = {}

    nc_file = get_first_nc_file(dir_path)
    if nc_file:
        qc_var_types = check_for_qc_vars(nc_file)
    else:
        qc_var_types = {'gen_qc': {}, 'qartod': {}}


    # variables which need to have the variable {var_name}_qc present in the
    # template.  Right now these are all the same, so are hardcoded
    required_qc_vars = ("conductivity_qc", "density_qc", "depth_qc",
                        "latitude_qc", "lat_uv_qc", "longitude_qc",
                        "lon_uv_qc", "profile_lat_qc", "profile_lon_qc",
                        "pressure_qc", "salinity_qc", "temperature_qc",
                        "time_qc", "time_uv_qc", "profile_time_qc",
                        "u_qc", "v_qc")

    # any destinationNames that need to have a different name.
    # by default the destinationName will equal the sourceName
    dest_var_remaps = {'longitude_qc': 'precise_lon_qc',
                       'latitude_qc': 'precise_lat_qc',
                       'profile_lon_qc': 'longitude_qc',
                       'profile_lat_qc': 'latitude_qc',
                       'time_qc': 'precise_time_qc',
                       'profile_time_qc': 'time_qc'}

    templ = template.render(dataset_id=deployment,
                           dataset_dir=dir_path,
                           institution=institution,
                           checksum=checksum,
                           completed=completed,
                           reqd_qc_vars=required_qc_vars,
                           dest_var_remaps=dest_var_remaps,
                           qc_var_types=qc_var_types)
    if not extra_atts:
        return templ

    else:

        try:
            tree = etree.fromstring(templ)
            for identifier, mod_attrs in extra_atts.iteritems():
                add_extra_attributes(tree, identifier, mod_attrs)

            return etree.tostring(tree)

        except:
            logger.exception()
            return templ



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

    for att_name, value in mod_atts.iteritems():
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


def get_first_nc_file(root):
    '''
    Returns the first netCDF file found in the directory

    :param str root: Root of the directory to scan
    '''
    for content in os.listdir(root):
        if content.endswith('.nc'):
            return os.path.join(root, content)


def check_for_qc_vars(nc_file):
    """
    Checks for general gc variables and QARTOD variables by naming conventions.
    Returns a dict with both sets of variables as keys, and their attributes
    as values.
    """
    # STYLE: shouldn't this go at the top of the file?
    from netCDF4 import Dataset
    qc_vars = {'gen_qc': {}, 'qartod': {}}
    with Dataset(nc_file, 'r') as nc:
        for var in nc.variables:
            if var.endswith('_qc'):
                qc_vars['gen_qc'][var] = nc.variables[var].ncattrs()
            elif var.startswith('qartod'):
                qc_vars['qartod'][var] = nc.variables[var].ncattrs()
    return qc_vars


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

