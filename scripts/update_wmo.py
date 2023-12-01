#!/usr/bin/env python
'''
scripts/update_wmo.py

A script to get WMO IDs and attribution from netCDF files and apply them to the dataset in mongo
'''

from glider_dac import app, db
from netCDF4 import Dataset
import sys

def main(args):
    '''
    Parse WMO IDs from netCDF files and update mongo records
    '''
    # For each deployment without a wmo id
    for deployment in db.Deployment.find({"$or":[{"wmo_id":None}, {"attribution":None}]}):
        try:
            update_deployment(deployment)
        except Exception as e:
            continue

    return 0


def update_deployment(deployment):
    '''
    Returns an updated deployment with the fields filled in where necessary.

    :param Deployment deployment: The deployment object
    '''
    dap_url = deployment.dap
    dirty = False

    with Dataset(dap_url) as nc:

        if deployment.wmo_id is None:
            wmo_id = get_wmo(nc)
            if wmo_id:
                deployment.wmo_id = wmo_id
                dirty = True

        elif deployment.attribution is None:
            attribution = get_acknowledgment(nc)
            if attribution:
                deployment.attribution = attribution
                dirty = True

        if dirty:
            deployment.save()


def get_wmo(nc):
    '''
    Gets the best candidate for a WMO ID

    :param netCDF4.Dataset nc: An open netCDF4 Dataset
    '''
    if getattr(nc, 'wmo_id', None):
        wmo_id = nc.wmo_id
    elif 'wmo_id' in nc.variables:
        wmo_id = ''.join(nc.variables['wmo_id'][:].flatten())
    else:
        return None
    return wmo_id


def get_acknowledgment(nc):
    '''
    Gets the best candidate for an acknowledgment

    :param netCDF4.Dataset nc: An open netCDF4 Dataset
    '''
    return getattr(nc, 'acknowledgment', None)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description=main.__doc__)

    args = parser.parse_args()
    with app.app_context():
        sys.exit(main(args))
