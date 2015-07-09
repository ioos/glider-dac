#!/usr/bin/env python
'''
'''
from config import API_URL, NCEI_DIR, path2pub
import json
import requests
import argparse
import sys
import os

def get_deployments():
    r = requests.get(API_URL)
    if r.status_code != 200:
        raise IOError("Failed to get deployments from API")
    return r.json()

def get_active_deployments():
    deployments = get_deployments()
    filtered = [d for d in deployments['results'] if d['completed']]
    for d in filtered:
        filedir = os.path.join(path2pub, d['deployment_dir'])
        filename = os.path.basename(d['deployment_dir']) + '.ncCF.nc3.nc'
        filepath = os.path.join(filedir, filename)
        make_link(filepath)

def make_link(filepath):
    filename = os.path.basename(filepath)
    target = os.path.join(NCEI_DIR, filename)
    source = filepath
    os.symlink(source, target)


def main(args):
    get_active_deployments()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=main.__doc__)
    args = parser.parse_args()
    sys.exit(main(args))


        
