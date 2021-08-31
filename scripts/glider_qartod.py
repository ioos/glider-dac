#!/usr/bin/env python
'''
scripts/glider_qartod.py
'''
from argparse import ArgumentParser
from netCDF4 import Dataset
from glider_qc import glider_qc
from rq import Queue, Connection, Worker
import logging
import os
import time

from glider_dac.common import log_format_str


def acquire_master_lock():
    '''
    Acquire the master lock or raise an exception
    '''
    rc = glider_qc.get_redis_connection()
    lock = rc.lock('gliderdac:glider_qartod', blocking_timeout=60)
    return lock


def clear_master_lock():
    '''
    Clears the master lock regardless if it is acquired
    '''
    rc = glider_qc.get_redis_connection()
    rc.delete('gliderdac:glider_qartod')


def sync_lock():
    '''
    Locks the process while a deployment sync is in progress
    '''
    while os.path.exists('/tmp/deployment-sync'):
        glider_qc.log.info("Waiting for sync to finish")
        time.sleep(10)


def main():
    '''
    Apply QARTOD QC to GliderDAC submitted netCDF files

    Example::

        python scripts/glider_qartod.py -c data/qc_config.yml ~/Desktop/revellie/revellie.nc

    '''
    args = get_args()
    if args.clear:
        clear_master_lock()
        return 0
    if args.worker:
        with Connection(glider_qc.get_redis_connection()):
            worker = Worker(list(map(Queue, ['gliderdac'])))
            worker.work()
        return 0

    lock = acquire_master_lock()
    if not lock.acquire():
        raise glider_qc.ProcessError("Master lock already held by another process")
    try:
        file_paths = []
        if args.verbose:
            setup_logging()

        if args.recursive:
            file_paths = get_files(args.netcdf_files)
        else:
            file_paths = args.netcdf_files

        if args.config is None:
            raise ValueError("No configuration found, please set using -c")

        process(file_paths, args.config, sync=args.sync)
    finally:
        lock.release()

    return 0


def process(file_paths, config, sync=False):
    queue = Queue('gliderdac', connection=glider_qc.get_redis_connection())

    for nc_path in file_paths:
        sync_lock()
        try:
            glider_qc.log.info("Inspecting %s", nc_path)
            with Dataset(nc_path, 'r') as nc:
                if not glider_qc.check_needs_qc(nc):
                    continue

            glider_qc.log.info("Applying QC to dataset %s", nc_path)

            if sync:
                glider_qc.qc_task(nc_path, config)
            else:
                queue.enqueue(glider_qc.qc_task, nc_path, config)
        except Exception as e:
            glider_qc.log.exception("Failed to check %s for QC", nc_path)


def get_args():
    parser = ArgumentParser(description=main.__doc__)
    parser.add_argument('-w', '--worker', action='store_true', help='Launch a worker')
    parser.add_argument('-r', '--recursive', action='store_true', help='Iterate through the directory contents recursively')
    parser.add_argument('-c', '--config', help='Path to config YML file to use')
    parser.add_argument('-v', '--verbose', action='store_true', help='Turn on logging')
    parser.add_argument('--sync', action='store_true', help='Run the jobs synchronously')
    parser.add_argument('--clear', action='store_true', help='Clear all locks')
    parser.add_argument('netcdf_files', nargs='*', help='NetCDF file to apply QC to')

    args = parser.parse_args()
    return args


def get_files(netcdf_files):
    '''
    Returns all of the netCDF files found in the directory recursively

    :param str netcdf_files: Directory of the netCDF files
    '''
    file_paths = []
    for netcdf_dir in netcdf_files:
        if netcdf_dir.endswith("-delayed"):
            continue
        for (path, dirs, files) in os.walk(netcdf_dir):
            for filename in files:
                if filename.endswith('.nc'):
                    file_paths.append(os.path.join(path, filename))
    return file_paths


def setup_logging(
    default_path=None,
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration
    """
    logging.basicConfig(format=log_format_str, level=default_level)

if __name__ == '__main__':
    main()
