#!/usr/bin/env python
'''

'''

from glider_dac import app, db
import argparse
import sys
import os
import shutil

def main(args):
    src = args.src
    dest = args.dest

    update_db(src, dest)
    update_catalog(app.config["PUBLIC_CATALOG"], src, dest)
    update_catalog(app.config["PRIVATE_CATALOG"], src, dest)
    update_filesystem(app.config["path2priv"], src, dest)
    update_filesystem(app.config["path2pub"], src, dest)
    update_filesystem(app.config["path2thredds"], src, dest)

def update_db(src, dest):
    with app.app_context():
        provider, deployment_name = deployment_split(src)
        d_provider, d_deployment_name = deployment_split(dest)
        deployments = list(db.Deployment.find({'name':deployment_name}))
        for dep in deployments:
            print(dep.name, '->', d_deployment_name)
            dep.name = str(d_deployment_name)
            print(dep.deployment_dir, '->', dest)
            dep.deployment_dir = str(dest)
            dep.save()

def update_catalog(catalog_loc, src, dest):
    catalog_dir, xml_file = os.path.split(catalog_loc)
    swp_file = os.path.join(catalog_dir, xml_file + '.swp')
    provider, deployment_name = deployment_split(src)
    d_provider, d_deployment_name = deployment_split(dest)

    with open(catalog_loc, 'r') as f, open(swp_file, 'w') as swp:
        for i, line in enumerate(f):
            if src in line:
                print('XML:%s:%s' % (catalog_loc, i), src, '->', dest)
                line = line.replace(src, dest)
                print(line)
            elif deployment_name in line:
                print('XML:%s:%s' % (catalog_loc, i), deployment_name, '->', d_deployment_name)
                line = line.replace(deployment_name, d_deployment_name)
                print(line)
            swp.write(line)
    shutil.move(swp_file, catalog_loc)

def update_filesystem(root, src, dest):
    if os.path.exists(os.path.join(root, src)):
        print('Filesystem: mv %s %s' % (os.path.join(root, src), os.path.join(root, dest)))
        shutil.move(os.path.join(root, src), os.path.join(root, dest))

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

