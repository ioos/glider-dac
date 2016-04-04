#!/usr/bin/env python
'''
scripts/update_wmo.py

A script to get WMO IDs from netCDF files and apply them to the dataset in mongo
'''

from glider_dac import app, db
from netCDF4 import Dataset
import sys

def main(args):
    '''
    Parse WMO IDs from netCDF files and update mongo records
    '''
    # For each deployment without a wmo id
    for deployment in db.Deployment.find({u"wmo_id":None}):
        try:
            wmo_id = determine_wmo_id(deployment)
            deployment.wmo_id = wmo_id
            deployment.save()
        except Exception as e:
            continue

    return 0


def determine_wmo_id(deployment):
    '''
    Returns the wmo_id as written in the netCDF files
    :param Deployment deployment: The deployment object
    '''
    dap_url = deployment.dap
    with Dataset(dap_url) as nc:
        if hasattr(nc, 'wmo_id'):
            wmo_id = nc.wmo_id
        elif 'wmo_id' in nc.variables:
            wmo_id = ''.join(nc.variables['wmo_id'][:].flatten())
        return wmo_id


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description=main.__doc__)

    args = parser.parse_args()
    with app.app_context():
        sys.exit(main(args))

