#!/usr/bin/env python
import aiohttp
import argparse
import async_timeout
import asyncio
import calendar
import datetime
import glob
import json
import logging
import os
import sys
import time
from datetime import datetime
from netCDF4 import Dataset

from config import *
log = None


def setup_logging(level=logging.DEBUG):
    import logging
    logger = logging.getLogger('replicate')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('replciate.log')
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)
    return logger


def main(args):
    '''
    '''
    acquire_lock(args.lock_file)
    try:
        global log
        if log is None:
            log = setup_logging()
        if args.deployment is not None:
            deployments = [args.deployment]
        else:
            deployments = get_deployments()

        log.info( "Processing the following deployments")
        for deployment in deployments:
            log.info( " - %s", deployment)
        # limit to 4 simultaneous connections open for fetching data
        sem = asyncio.Semaphore(4)
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(sync_deployment(d, sem, args.force))
                 for d in deployments]
        wait_tasks = asyncio.wait(tasks)
        loop.run_until_complete(wait_tasks)
        loop.close()

    finally:
        release_lock(args.lock_file)


async def sync_deployment(deployment, sem, force=False):
    '''
    For a given deployment (dataset), if it's got new data, use the
    ERDDAP flagging system to notify ERDDAP
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
            pass  # Causes file creation (touch)

    log.info( "--------------------------------------------------------------------------------")
    log.info( "   Processing %s", deployment)
    log.info( "--------------------------------------------------------------------------------")
    d = deployment
    # Get Current Epoch Time and how far back in time to search
    currentEpoch = time.time()
    # reload any datasets which have been updated in the last 24 hours
    time_in_past = 3600 * 24
    mTime = get_mod_time(d)
    deltaT = int(currentEpoch) - int(mTime)

    log.info( "Synchronizing at %s", datetime.utcnow().isoformat())
    if force or deltaT < time_in_past:
        deployment_name = deployment.split('/')[-1]
        # First sync up the private
        touch_erddap(deployment_name, flags_private)
        log.info("Sleeping 10 seconds")
        await asyncio.sleep(10)
        if not await poll_erddap(deployment_name, erddap_private):
            log.error("Couldn't update deployment %s", deployment)
            return
    else:
        log.info("Everything is up to date")


async def poll_erddap(deployment_name, host, proto='http', attempts=3):
    args = {}
    args['host'] = host
    args['deployment_name'] = deployment_name
    args['proto'] = proto
    url = '%(proto)s://%(host)s/erddap/tabledap/%(deployment_name)s.das' % args
    log.info("Polling %s", url)
    att_counter = attempts
    try:
        async with aiohttp.ClientSession() as session:
            while att_counter > 0:
                try:
                    async with session.get(url) as response:
                        if response.status != 200:
                            log.warning("Failed to find deployment dataset: {}".format(url))
                        else:
                            break
                except Exception:
                    log.exception("hit exception while processing for deployment {}".format(url))
                log.info("sleeping 15 second(s)")
                await asyncio.sleep(15)
                att_counter -= 1
            else:
                return False
            return True
    except Exception:
        log.exception("Error while fetching http for deployment {}".format(url))
        return False


def get_deployments():
    """Returns a list of the deployment directories"""
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
    except ValueError:
        # if there are no nc files, arbitrarily set time as 0
        newest = 0
    ncTime = os.path.getmtime(newest)
    if not os.path.exists(jsonFile):
        with open(jsonFile, 'w') as outfile:
            json.dump({'updated': ncTime * 1000}, outfile)
        log.info("Initiated JSON file: {}".format(outfile))

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
    parser = argparse.ArgumentParser(description="Sync the ERDDAP datasets")
    parser.add_argument('-l', '--lock-file', default='/tmp/replicate.lock', help='Lockfile to synchronize processes')
    parser.add_argument('-f', '--force', action="store_true", help="Force the processing of all datasets")
    parser.add_argument('-d', '--deployment', help="Manually load a specific deployment")
    args = parser.parse_args()
    main(args)
