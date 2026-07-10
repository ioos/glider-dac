#!/usr/bin/env python
'''
scripts/update_wmo.py

A script to get WMO IDs and attribution from netCDF files and apply them to the dataset in mongo
'''

from glider_dac import create_app
from glider_dac.models.deployment import Deployment
from netCDF4 import Dataset
import sys
from sqlalchemy import or_
import logging
import pandas as pd

def main(args):
    '''
    Parse WMO IDs from netCDF files and update mongo records
    '''
    # For each deployment without a wmo id
    for deployment in Deployment.query.filter(or_(Deployment.wmo_id.is_(None),
                                Deployment.attribution.is_(None))).all():
        print(deployment)
        try:
            update_deployment(deployment)
        except Exception:
            logging.exception("Encountered error attempting to set WMO ID/"
                             "attribution for {deployment.name}")
            continue

    return 0


def update_deployment(deployment):
    """
    Returns an updated deployment with the fields filled in where necessary.

    :param Deployment deployment: The deployment object
    """
    import re
    import requests

    def get_erddap_attr(erddap_url, attr_name):
        das_url = erddap_url.rsplit(".", 1)[0] + ".das"
        resp = requests.get(das_url, timeout=30)
        resp.raise_for_status()

        pattern = rf'(?<=String {attr_name} ")[^"]+'
        m = re.search(pattern, resp.text)
        return m.group(0) if m else None

    dirty = False

    if deployment.wmo_id is None:
        wmo_id = get_erddap_attr(deployment.erddap, "wmo_id")
        if wmo_id:
            deployment.wmo_id = wmo_id
            dirty = True

    if deployment.attribution is None:
        attribution = get_erddap_attr(deployment.erddap, "acknowledgment")
        if attribution:
            deployment.attribution = attribution
            dirty = True

    if dirty:
        deployment.save()

        print(f"Modified deployment {deployment.name}")

    return deployment


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description=main.__doc__)

    args = parser.parse_args()
    with create_app().app_context():
        sys.exit(main(args))
