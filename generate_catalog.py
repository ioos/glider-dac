#!/usr/bin/env python
import os
import time
import shutil
import argparse
import subprocess
from lxml import etree    

DATA_ROOT = os.environ.get("DATA_ROOT", "/home/dev/Development/glider-mission/test")
DEV_CATALOG_ROOT = os.environ.get("DEV_CATALOG_ROOT", "/home/dev/Development/glider-mission/test/thredds")
PROD_CATALOG_ROOT = os.environ.get("PROD_CATALOG_ROOT", "/home/dev/Development/glider-mission/test/prod")

def update_thredds_catalog(base, dev, prod):
    catalog_ns  = "http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"
    xlink_ns    = "http://www.w3.org/1999/xlink"

    nsmap = {
        None    :  catalog_ns,
        "xlink" :  xlink_ns
    }

    catalog_paths = []

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
                    # (the catalog scripts could have been updated since the first time they were generated)
                    os.utime(mission_dir, None)

                    # Mission specific THREDDS catalog file
                    catalog_paths.append((user, mission))

    # Wait for any catalog to be generated that need to be
    time.sleep(30)

    # Create catalog file including all missions
    with open(os.path.join(dev, 'catalog.xml'), 'wb') as f:

        root = etree.Element("{%s}catalog" % catalog_ns, nsmap=nsmap)
        root.set("name", "IOOS Glider DAC - Catalog")

        for cat in catalog_paths:
            # Create mission catalogRef
            catalog_ref = etree.Element("{%s}catalogRef" % catalog_ns, nsmap=nsmap)
            catalog_ref.set("{%s}href" % xlink_ns,  os.path.join(dev, cat[0], cat[1], "catalog.xml"))
            catalog_ref.set("{%s}title" % xlink_ns, "%s - %s" % (cat[0], cat[1]))
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
    subprocess.call(["git", "checkout", "master"])
    subprocess.call(["git", "add", "."])
    subprocess.call(["git", "commit", "-m", "Automated catalog update"])
    subprocess.call(["git", "pull", "origin", "master"])
    subprocess.call(["git", "push", "origin", "master"])
    subprocess.call(["git", "push", "origin", "master"])
    shutil.copyfile(os.path.join(dev, 'catalog.xml'), os.path.join(prod, 'catalog.xml'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('basedir',
                        default=DATA_ROOT,
                        nargs='?')
    parser.add_argument('devcatalogdir',
                        default=DEV_CATALOG_ROOT,
                        nargs='?')
    parser.add_argument('prodcatalogdir',
                        default=PROD_CATALOG_ROOT,
                        nargs='?')
    args = parser.parse_args()
    base = os.path.realpath(args.basedir)
    dev = os.path.realpath(args.devcatalogdir)
    prod = os.path.realpath(args.prodcatalogdir)

    update_thredds_catalog(base, dev, prod)
    