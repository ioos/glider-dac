#!/usr/bin/env python
import aiohttp
import argparse
import async_timeout
import asyncio
import calendar
import glob
import json
import logging
import os
import sys
import time
from datetime import datetime
from netCDF4 import Dataset

from config import *
from glider_dac.common import log_formatter
log = None


def setup_logging(level=logging.DEBUG):
    logger = logging.getLogger('replicate')
    logger.setLevel(level)
    file_handler = logging.FileHandler('replicate.log')
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(log_formatter)
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(level)
    return logger


def main(args):
    '''
    This script loops through deployments and fetches a single .ncCF (public ERDDAP)
    or .ncCFMA (THREDDS) file to serve via ERDDAP/THREDDS

    This process can be VERY CPU intensive.
    '''
    acquire_lock(args.lock_file)
    try:
        global log
        if log is None:
            level = logging.DEBUG if args.verbose else logging.ERROR
            log = setup_logging(level)
        if args.deployment is not None:
            deployments = [args.deployment]
        else:
            deployments = get_deployments()

        log.info( "Processing the following deployments")
        for deployment in deployments:
            if not deployment.endswith("-delayed"):
                log.info( " - %s", deployment)
        # limit to 8 simultaneous connections open for fetching data
        # badams (2020-07-30) limit to two concurrent processes to avoid bogging down server
        sem = asyncio.Semaphore(2)
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(sync_deployment(d, sem, args.force))
                 for d in deployments
                 if not d.endswith("-delayed")]
        wait_tasks = asyncio.wait(tasks)
        loop.run_until_complete(wait_tasks)
        loop.close()

    finally:
        release_lock(args.lock_file)


async def sync_deployment(deployment, sem, force=False):
    '''
    For a given deployment (dataset), check if it's got new data and
    fetch the aggregated dataset for ERDDAP/THREDDS
    '''
    def touch_erddap(deployment_name, path):
        '''
        Creates a flag file for erddap's file monitoring thread so that it reloads
        the dataset

        path should be from config either flags_private or flags_public
        '''
        full_path = os.path.join(path, deployment_name)
        log.info("Touching flag file at %s", full_path)
        # technically could async this as it's I/O, but touching a file is pretty
        # unlikely to be a bottleneck
        with open(full_path, 'w') as f:
            pass  # Causes file creation

    # Get Current Epoch Time and how far back in time to search
    currentEpoch = time.time()
    # reload any datasets which have been updated in the last 24 hours
    time_in_past = 3600 * 24
    mTime = get_mod_time(deployment)
    deltaT = int(currentEpoch) - int(mTime)

    if force or deltaT < time_in_past:
        log.info( "--------------------------------------------------------------------------------")
        log.info( "   Processing %s", deployment)
        log.info( "--------------------------------------------------------------------------------")
        log.info( "Synchronizing at %s", datetime.utcnow().isoformat())
        deployment_name = deployment.split('/')[-1]

        # TODO deprecate this second ERDDAP!
        await retrieve_data(path2pub, deployment, sem)

        touch_erddap(deployment_name, flags_public)

        await retrieve_data(path2thredds, deployment, sem)


async def retrieve_data(where, deployment, sem, proto='http'):
    '''
    '''
    publish_dir = os.path.join(where, deployment)
    log.info("Publish Directory: %s", publish_dir)
    deployment_name = publish_dir.split('/')[-1]
    user_name = publish_dir.split('/')[-2]
    if 'thredds' in publish_dir:
        path_arg = os.path.join(publish_dir, deployment_name + ".nc3.nc")
        url = '{}://{}/erddap/tabledap/{}.ncCFMA'.format(proto, erddap_private, deployment_name)
    else:
        path_arg = os.path.join(publish_dir, deployment_name + ".ncCF.nc3.nc")
        url = '{}://{}/erddap/tabledap/{}.ncCF'.format(proto, erddap_private, deployment_name)
    log.info("Path Arg %s", path_arg)
    log.info("Host Arg %s", url)

    fail_counter = 5
    # try to release semaphore before attempting to get the response
    async with sem:
        try:
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                while True:
                    try:
                        # This causes timeouts even when the max simultaneous connection
                        # lock isn't released
                        async with session.get(url) as response:
                            with open(path_arg + '.tmp', 'wb') as f_handle:
                                while True:
                                    chunk = await response.content.read(1024)
                                    if not chunk:
                                        break
                                    f_handle.write(chunk)
                            try:
                                log.info(os.stat(path_arg + '.tmp'))
                                # sanity check to ensure netCDF file is valid
                                with Dataset(path_arg + '.tmp') as d:
                                    pass
                            except Exception:
                                log.exception("Exception while attempting to open NetCDF dataset {}".format(path_arg + '.tmp'))
                                os.unlink(path_arg + '.tmp')
                            else:
                                os.rename(path_arg + '.tmp', path_arg)

                                # if the download succeeded and file isn't corrupt, replace the previous file
                                log.info(("moved file {}".format(path_arg + '.tmp')))
                            return await response.release()
                    except Exception as e:
                        fail_counter -= 1
                        log.exception("Failed to get %s", deployment)
                        log.info("Attempts remainging: %s", fail_counter)
                        if fail_counter <= 0:
                            break

        except Exception:
            log.exception("HTTP issue occurred while fetching data for {}".format(deployment))
            os.unlink(path_arg + '.tmp')


def get_deployments():
    '''
    Loads deployment directories into a list
    '''
    deployments = []
    for user in os.listdir(path2priv):
        if not os.path.isdir(os.path.join(path2priv, user)):
            continue
        for deployment_name in os.listdir(os.path.join(path2priv, user)):
            deployment_path = os.path.join(path2priv, user, deployment_name)
            if os.path.isdir(deployment_path):
                deployments.append(os.path.join(user, deployment_name))
    return deployments


def get_mod_time(name):

    jsonFile = os.path.join(JSON_DIR, name + '/deployment.json')
    log.info("Inspecting %s", jsonFile)

    try:
        newest = max(glob.iglob(JSON_DIR + name + '/' + '*.nc') , key=os.path.getmtime)
        ncTime = os.path.getmtime(newest)
    # if there are no nc files, arbitrarily set time as 0
    except ValueError:
        ncTime = 0

    if not os.path.exists(jsonFile):
        log.info( "JSON file does not exist.")
        with open(jsonFile, 'w') as outfile:
            json.dump({'updated': ncTime * 1000}, outfile)
        log.info("Initiated JSON file")

    with open(jsonFile, 'r') as fid:
        dataset = json.load(fid)
    # get the max time reported between the netCDF files and the update time
    # in the deployments json file
    update_time = max(ncTime * 1000, dataset['updated'])
    update_timestring = datetime.fromtimestamp(update_time / 1000).isoformat()
    log.info("Dataset {} last updated {}".format(name, update_timestring))
    return update_time / 1000


def acquire_lock(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            str_pid = f.read()
        pid = int(str_pid)
        if check_pid(pid):
            raise IOError("Lock is already aquired")

    with open(path, 'w') as f:
        f.write("{}\n".format(os.getpid()))


def release_lock(path):
    os.unlink(path)


def check_pid(pid):
    """
    Check For the existence of a unix pid.

    :param int pid: Process ID
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="replicate files from private ERDDAP")
    parser.add_argument('-l', '--lock-file', default='/tmp/replicate.lock', help='Lockfile to synchronize processes')
    parser.add_argument('-f', '--force', action="store_true", help="Force the processing by ignoring the time logs")
    parser.add_argument('-d', '--deployment', help="Load a specific deployment")
    parser.add_argument('-v', '--verbose', action="store_true", help="Sets log level to debug")

    args = parser.parse_args()
    main(args)
