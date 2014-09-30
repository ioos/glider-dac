#!/usr/bin python

import boto
import boto.s3
from boto.s3.key import Key
import sys
import os
import json

# S3 stuff
AWS_ACCESS_KEY_ID = 'AKIAJEYHTZSDVJTSILDQ'
AWS_SECRET_ACCESS_KEY = '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'

bucket_name = 'ioosgliderbackups'
conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
bucket = conn.create_bucket(bucket_name, location=boto.s3.connection.Location.DEFAULT)

# Define backup filename
backup_file = os.path.dirname(os.path.abspath(__file__)) + '/backup.txt'


def upload(filenames=[]):
    ''' Upload to S3 bucket'''

    def percent_cb(complete, total):
        sys.stdout.write('.')
        sys.stdout.flush()

    for filename in filenames:
        print 'Uploading %s to Amazon S3 bucket %s\n' % (filename, bucket_name)
        k = Key(bucket)
        k.key = filename
        try:
            k.set_contents_from_filename(filename, cb=percent_cb, num_cb=10)
        except Exception as e:
            print str(e)


def check_file(data, filename, mod_time):
    '''Compare file against the backup json file'''

    if filename in data:
        # Has this file been modified?
        if data[filename] != mod_time:
            data[filename] = mod_time
            update_json(data)
            upload([filename])
    else:
        # This is a new file
        data[filename] = mod_time
        update_json(data)
        upload([filename])


def update_json(data):
    ''' Update the backup json file'''
    with open(backup_file, 'w') as f:
        json.dump(data, f)


def backup_files(root):
    '''This is the meat and potatoes. Scan the root directory for new/modified files'''

    root_dir = root

    if os.path.isfile(backup_file):
        # Standard operting procedure:
        # Walk the directory, compare against the backup json file
        # If necessary backup to S3

        with open(backup_file, 'r') as f:
            data = json.load(f)

        for dirpath, dirnames, filenames in os.walk(root_dir):
            for f in filenames:
                filepath = os.path.join(dirpath, f)
                # Check if it has been modified in last day
                mod_time = os.path.getmtime(filepath)
                check_file(data, filepath, mod_time)
    else:
        # This must be the first time a backup has been scheduled
        # Create the json file and upload all files
        json_data = {}
        for dirpath, dirnames, filenames in os.walk(root_dir):
            for f in filenames:
                filepath = os.path.join(dirpath, f)
                mod_time = os.path.getmtime(filepath)
                json_data[filepath] = mod_time

        update_json(json_data)
        upload(json_data.keys())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: %s [directory] [backup directory]" % sys.argv[0])
    root_dirs = []

    # if len(sys.argv) >= 3:
    for n in range(1, len(sys.argv)):
        root_dirs.append(os.path.abspath(os.path.expanduser(os.path.expandvars(sys.argv[n]))))

    for root_dir in root_dirs:
        if os.path.isdir(root_dir):
            backup_files(root_dir)
        else:
            print root_dir + " does not exist"
