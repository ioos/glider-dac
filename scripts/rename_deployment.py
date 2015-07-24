#!/usr/bin/env python
'''

'''

from glider_dac import app, db
import argparse
import sys
import os



def main(args):
    src = args.src
    dest = args.dest

    update_db(src, dest)

def update_private_erddap(src, dest):
    pass

def update_db(src, dest):
    with app.app_context():
        provider, deployment_name = deployment_split(deployment)
        d_provider, d_deployment_name = deployment_split(deployment)
        deployments = list(db.Deployment.find({'name':deployment_name}))
        for dep in deployments:
            print "Moving ", dep.name, 'to', d_deployment_name
            print dep.deployment_dir, '->', dest

def deployment_split(deployment):
    '''
    Returns a tuple (provider, deployment_name)
    '''
    return deployment.split('/')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('src', help='Source deployment name')
    parser.add_argument('dest', help='Destination deployment name')
    args = parser.parse_args()
    sys.exit(main(args))

