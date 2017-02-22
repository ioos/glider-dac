#!/usr/bin/env python
'''
Script to create symlinks of archivable datasets and generate an MD5 sum
'''
from config import API_URL, NCEI_DIR, path2pub
import requests
import argparse
import sys
import os
import hashlib
import logging
import shutil

logger = logging.getLogger('archive_datasets')


def get_deployments():
    '''
    Returns an HTTP GET request for the API_URL
    '''
    r = requests.get(API_URL)
    if r.status_code != 200:
        raise IOError("Failed to get deployments from API")
    return r.json()


def get_active_deployments():
    '''
    Yields a filepath for each deployment marked completed by the API
    '''
    deployments = get_deployments()
    filtered = [d for d in deployments['results'] if d['completed']]
    for d in filtered:
        if 'archive_safe' in d and d['archive_safe'] is False:
            continue
        filedir = os.path.join(path2pub, d['deployment_dir'])
        filename = os.path.basename(d['deployment_dir']) + '.ncCF.nc3.nc'
        filepath = os.path.join(filedir, filename)
        yield filepath


def make_copy(filepath):
    '''
    Creates a symbolic link of the file specified in the new NCEI_DIR
    :param str filepath: Path to the source of the symbolic link
    '''
    filename = os.path.basename(filepath)
    target = os.path.join(NCEI_DIR, filename)
    source = filepath
    if not os.path.exists(target):
        logger.info("Creating archive dataset")
        shutil.copyfile(source, target)
    generate_hash(target)


def generate_hash(filepath):
    '''
    Creates an MD5 sum file containing the hash of the file
    :param str filepath: Path to the file to be hashed
    '''
    hasher = hashlib.md5()
    hashfile(filepath, hasher)
    md5sum = filepath + '.md5'
    with open(md5sum, 'w') as f:
        f.write(hasher.hexdigest())
    logger.info("Hash generated")


def hashfile(filepath, hasher, blocksize=65536):
    '''
    Uses a memory efficient scheme to hash a file
    :param str filepath: Path to the file to be hashed
    :param hashlib.algorithm hasher: The hasher to use
    :param int blocksize: Size in bytes of the memory segment
    '''
    with open(filepath, 'r') as f:
        buf = f.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(blocksize)
    return hasher


def set_verbose():
    '''
    Enables console logging
    '''
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)


def remove_archive(deployment):
    '''
    Removes a deployment from the archive

    :param str deployment: Deployment name
    '''
    filename = '{}.ncCF.nc3.nc'.format(deployment)
    path = os.path.join(NCEI_DIR, filename)
    logger.info("Removing archive: %s", deployment)
    if os.path.exists(path + '.md5'):
        os.unlink(path + '.md5')
    if os.path.exists(path):
        os.unlink(path)


def main(args):
    '''
    Script to create symlinks of archivable datasets and generate an MD5 sum
    '''
    if args.verbose:
        set_verbose()
    active_deployments = list(get_active_deployments())
    for filepath in active_deployments:
        logger.info("Archiving %s", filepath)
        make_copy(filepath)

    for filename in os.listdir(NCEI_DIR):
        if filename.endswith('.ncCF.nc3.nc'):
            deployment = filename.split('.')[0]
            if deployment not in active_deployments:
                remove_archive(deployment)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('-v', '--verbose', action='store_true', help='Turn on verbose output')
    args = parser.parse_args()
    sys.exit(main(args))


        
