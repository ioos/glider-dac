#!/usr/bin python
#-*- conding: utf-8 -*-
import boto
import boto.s3
from boto.s3.key import Key
import sys
import os
from dateutil.parser import parse as dateparse
from datetime import datetime
import logging
import hashlib
import pwd
import argparse
from glider_dac import log_formatter

logger = logging.getLogger('back_to_s3')

# S3 stuff

conn = boto.connect_s3(app.config["AWS_ACCESS_KEY_ID"],
                       app.config["AWS_SECRET_ACCESS_KEY"])
bucket = conn.create_bucket(app.config["BUCKET_NAME"],
                            location=boto.s3.connection.Location.DEFAULT)

def hashfile(filepath, hasher, blocksize=65536):
    '''
    Returns a hash of a file
    :param str filepath: Path to the file being hashed
    :param hashlib.algorithm hasher: Algorithm to use for hashing
    :param int blocksize: Block size
    '''
    with open(filepath, 'rb') as f:
        buf = f.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(blocksize)
    return hasher

def push_file(filepath, relpath):
    '''
    Checks the mtime of the file and if it's been modified it pushes the entire file contents to the s3 bucket
    :param str filepath: The filesystem path to the file pending for upload
    :param str relpath: The root of the directory structure being backed up
    '''
    keyname = os.path.relpath(filepath, relpath)
    logger.info("Accessing S3 key %s", keyname)
    existing_key = key = bucket.get_key(keyname)
    local_mtime = datetime.utcfromtimestamp(os.path.getmtime(filepath))
    filestats = os.stat(filepath)
    if key is None:
        logger.info("Key doesn't exist, creating new key")
        key = Key(bucket)
        key.key = keyname
        key.set_metadata('username', pwd.getpwuid(filestats.st_uid).pw_name)
        key.set_metadata('unix-perms', oct(filestats.st_mode))

    if key.get_metadata('mtime') != local_mtime.isoformat() or existing_key is None:
        try:
            logger.info("Pushing %s (%.2f MB) to S3", keyname, os.path.getsize(filepath) * 1.0 / (1024 * 1024))
            md5sum = hashfile(filepath, hashlib.md5())
            logger.info("MD5 %s", md5sum.hexdigest())
            key.set_metadata('mtime', local_mtime.isoformat())
            key.set_metadata('md5', md5sum.hexdigest())
            key.set_contents_from_filename(filepath)
        except Exception as e:
            logger.exception("Failed to upload %s", filepath)
    else:
        logger.info("No changes necessary")

def backup_directory(directory):
    '''
    Walks the directory, looking for regular files. Each regular file is
    compared with S3 for the UNIX mtime, if the mtime is different on this
    host, then the file is pushed to s3.

    :param str directory: Directory to be backed up
    '''
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            push_file(filepath, directory)

def main():
    '''
    '''
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('directory', help='Path to the directory that will be backed up')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable logging')
    args = parser.parse_args()

    if args.verbose:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(log_formatter)
        logger.addHandler(ch)
        logger.setLevel(logging.DEBUG)

    backup_directory(args.directory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
