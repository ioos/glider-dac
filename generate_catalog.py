#!/usr/bin/env python
import os
import time
import json
import shutil
import argparse
import subprocess
from lxml import etree

RSYNC_TO_PATH = os.environ.get("RSYNC_TO_PATH")
DEV_CATALOG_ROOT = os.environ.get("DEV_CATALOG_ROOT")
PROD_CATALOG_ROOT = os.environ.get("PROD_CATALOG_ROOT")
DEBUG = False

def update_thredds_catalog(base, dev, prod, debug):
    catalog_ns  = "http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"
    xlink_ns    = "http://www.w3.org/1999/xlink"

    nsmap = {
        None    :  catalog_ns,
        "xlink" :  xlink_ns
    }

    # Create catalog file including all missions
    with open(os.path.join(dev, 'catalog.xml'), 'wb') as f:

        root = etree.Element("{%s}catalog" % catalog_ns, nsmap=nsmap)
        root.set("name", "IOOS Glider DAC - Catalog")

        # Iterate over Users
        for user in os.listdir(base):
            user_dir = os.path.join(base, user)
            if os.path.isdir(user_dir):
                # In User directory
                # Iterate over Missions
                for mission in os.listdir(user_dir):
                    mission_dir = os.path.join(user_dir, mission)
                    if os.path.isdir(mission_dir):
                        # In Mission directory
                        # Touch directory to make sure the catalogs get regenerated
                        # (the catalog generation scripts could have been updated since the first time they were generated)
                        os.utime(mission_dir, None)

                        # Load Misson JSON if is exists.  We want to pull information from this JSON
                        # and not rely on the directory structure if possible.
                        title        = user
                        mission_name = mission
                        mission_json = os.path.join(mission_dir, "mission.json")
                        if os.path.isfile(mission_json):
                            with open(mission_json) as m:
                                js           = json.load(m)
                                title        = js['operator']
                                if title is None or title == "":
                                    title = js['username']
                                mission_name = js['name']

                        title        = slugify(title)
                        mission_name = slugify(mission_name)

                        # Create mission catalogRef
                        catalog_ref = etree.Element("{%s}catalogRef" % catalog_ns, nsmap=nsmap)
                        catalog_ref.set("{%s}href" % xlink_ns,  os.path.join(user, mission, "catalog.xml"))
                        catalog_ref.set("{%s}title" % xlink_ns, "%s - %s" % (title, mission_name))
                        catalog_ref.set("name", "")
                        root.append(catalog_ref)

        # Add scratch directory
        catalog_ref = etree.Element("{%s}catalogRef" % catalog_ns, nsmap=nsmap)
        catalog_ref.set("{%s}href" % xlink_ns,  "scratch.xml")
        catalog_ref.set("{%s}title" % xlink_ns, "Scratch and Testing")
        catalog_ref.set("name", "")
        root.append(catalog_ref)

        f.write(etree.tostring(root, pretty_print=True))

    os.chdir(dev)
    if not debug:
        subprocess.call(["git", "checkout", "master"])
        subprocess.call(["git", "add", "."])
        subprocess.call(["git", "commit", "-m", "Automated catalog update"])
        subprocess.call(["git", "pull", "origin", "master"])
        subprocess.call(["git", "push", "origin", "master"])
    subprocess.call("rsync -r %s/* %s" % (dev, prod), shell=True)

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('basedir',
                        default=RSYNC_TO_PATH,
                        nargs='?')
    parser.add_argument('devcatalogdir',
                        default=DEV_CATALOG_ROOT,
                        nargs='?')
    parser.add_argument('prodcatalogdir',
                        default=PROD_CATALOG_ROOT,
                        nargs='?')
    parser.add_argument('debug',
                        default=DEBUG,
                        nargs='?')

    args = parser.parse_args()
    base = os.path.realpath(args.basedir)
    dev = os.path.realpath(args.devcatalogdir)
    prod = os.path.realpath(args.prodcatalogdir)
    debug = args.debug in ['true', 'True', 'TRUE', True]

    update_thredds_catalog(base, dev, prod, debug)
