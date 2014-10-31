#!/usr/bin/env python
import argparse
import json
import os
import sys
import urllib2
import argparse
import calendar
import time
import sh
import glob
import datetime
import logging
import requests

from config import *
log = None

def poll_erddap(deployment_name, host):
    args = {}
    args['host'] = host
    args['deployment_name'] = deployment_name
    url = 'http://%(host)s/erddap/tabledap/%(deployment_name)s.das' % args
    log.info("Polling %s", url)
    status = request_poll(url)
    return status

def request_poll(url, attempts=15):
    '''
    Polls a URL for the number of specified attempts
    returns True if the URL succeeded or False if it did not
    '''
    while attempts > 0:
        response = requests.get(url)
        if response.status_code != 200:
            log.warning("Failed to find deployment dataset")
        else:
            break
        log.info("sleeping 1 second")
        time.sleep(1)
        attempts -= 1
    else:
        return False
    return True



def touch_erddap(deployment_name, path):
    '''
    Creates a flag file for erddap's file monitoring thread so that it reloads
    the dataset

    path should be from config either flags_private or flags_public
    '''
    full_path = os.path.join(path, deployment_name)
    log.info("Touching flag file at %s", full_path)
    with open(full_path, 'w') as f:
        pass # Causes file creation
    log.info("Sleeping 15 seconds")
    time.sleep(15)


def setup_logging(level=logging.DEBUG):
    import logging
    logger = logging.getLogger('replicate')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('/home/glider/logs/replciate.log')
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler) 
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)
    return logger

def get_mod_time(name):

    jsonFile = os.path.join(JSON_DIR, name + '/deployment.json')
    log.info("Inspecting %s", jsonFile)

    if not os.path.exists(jsonFile):
        log.info( "JSON file does not exist.")
        newest = max(glob.iglob(JSON_DIR+name+'/'+'*.nc') , key=os.path.getmtime)
        jsonTime = os.path.getmtime(newest)
        with  open(jsonFile, 'w') as outfile:
            json.dump({'updated':jsonTime*1000}, outfile)
        log.info("Initiated JSON file")
        

    with open(jsonFile, 'r') as fid:
        dataset = json.load(fid)

    log.info( dataset['updated'])
    return (dataset['updated'])/1000

def main(args):
    '''
    '''
    global log
    if log is None:
        log = setup_logging()
    deployments = []
    for user in os.listdir(path2priv):
        if not os.path.isdir(os.path.join(path2priv, user)):
            continue
        for deployment_name in os.listdir(os.path.join(path2priv, user)):
            deployment_path = os.path.join(path2priv, user, deployment_name)
            if os.path.isdir(deployment_path):

                deployments.append(os.path.join(user, deployment_name))
            
    log.info( "Processing the following deployments")
    for deployment in deployments:
        log.info( " - %s", deployment)
    for deployment in deployments:
        sync_deployment(deployment, args.force)



def retrieve_data(where, deployment):
    '''
    '''
    publish_dir = os.path.join(where, deployment)
    log.info("Publish Directory: %s", publish_dir)
    deployment_name = publish_dir.split('/')[-1]
    user_name = publish_dir.split('/')[-2]
    if 'thredds' in publish_dir:
        path_arg = os.path.join(publish_dir, deployment_name + ".nc3.nc")
        host_arg = SERVER + "/tabledap/" + deployment_name + ".ncCFMA"
    else:
        path_arg = os.path.join(publish_dir, deployment_name + ".ncCF.nc3.nc")
        host_arg = SERVER + "/tabledap/" + deployment_name + ".ncCF"
    log.info( "Path Arg %s", path_arg)
    log.info( "Host Arg %s", host_arg)
    args = [
        "--no-host-directories",
        "--cut-dirs=2",
        "--output-document=%s" % path_arg,
        host_arg
     ]
    log.info( "Args: %s", ' '.join(args))
    sh.wget(*args)


def sync_deployment(deployment, force=False):
    '''
    '''
    log.info( "--------------------------------------------------------------------------------")
    log.info( "   Processing %s", deployment)
    log.info( "--------------------------------------------------------------------------------")
    d = deployment
    #Get Current Epoch Time and how far back in time to search
    currentEpoch = time.time()
    time_in_past = 3800
    mTime=get_mod_time(d)
    deltaT= int(currentEpoch) - int(mTime)
    log.info( "Synchronizing at %s", datetime.datetime.utcnow().isoformat())
    #print currentEpoch, deltaT, mTime
    if force or deltaT <  time_in_past: 
        deployment_name = deployment.split('/')[-1]
        # First sync up the private
        touch_erddap(deployment_name, flags_private)
        if not poll_erddap(deployment_name, erddap_private):
            log.error("Couldn't update deployment %s", deployment)
            return
        
        retrieve_data(path2pub, deployment)
        retrieve_data(path2thredds, deployment)

        touch_erddap(deployment_name, flags_public)
        if not poll_erddap(deployment_name, erddap_public):
            log.error("Couldn't update public erddap for deployment %s", deployment)
    else:
        log.info("Everything is up to date")
  
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="replicate files from private ERDDAP")
    parser.add_argument('-f', '--force', action="store_true")
    args = parser.parse_args()
    main(args)

