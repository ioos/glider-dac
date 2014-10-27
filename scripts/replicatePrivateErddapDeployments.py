#!/usr/bin/env python
import argparse
import json
import os
import sys
import urllib2
import feedparser
import calendar
import time
import sh
import glob
import datetime

from config import *


def get_mod_time(name):

    jsonFile = os.path.join(JSON_DIR, name + '/deployment.json')
    print "Inspecting", jsonFile

    if not os.path.exists(jsonFile):
        print "JSON file does not exist."
        newest = max(glob.iglob(JSON_DIR+name+'/'+'*.nc') , key=os.path.getmtime)
        jsonTime = os.path.getmtime(newest)
        with  open(jsonFile, 'w') as outfile:
            json.dump({'updated':jsonTime*1000}, outfile)
        print "Initiated JSON file"
        

    with open(jsonFile, 'r') as fid:
        dataset = json.load(fid)

    print dataset['updated']
    return (dataset['updated'])/1000

def main():
    deployments = []
    for u in os.listdir(path2priv):
        if os.path.isdir(path2priv+u):
            deployments.extend( [u+'/'+d for d in os.listdir(path2priv+u+'/')])
    print "Processing the following deployments"
    for d in deployments:
        print " -", d
    for d in deployments:
        sync_deployment(d)

def retrieve_data(where, d):
    ud=where+d
    pathDeployName = ud.split('/')[-1]
    path_arg = ud + "/" + pathDeployName + ".nc3.nc"
    host_arg = SERVER+"/tabledap/" + pathDeployName + ".ncCFMA"
    print "Path Arg", path_arg
    print "Host Arg", host_arg
    args = [
        "--no-host-directories",
        "--cut-dirs=2",
        "--output-document=%s" % path_arg,
        host_arg
     ]
    print "Args:", ' '.join(args)
    sh.wget(*args)


def sync_deployment(deployment):
    print "--------------------------------------------------------------------------------"
    print "   Processing", deployment
    print "--------------------------------------------------------------------------------"
    d = deployment
    #Get Current Epoch Time and how far back in time to search
    currentEpoch = time.time()
    time_in_past = 3800
    mTime=get_mod_time(d)
    deltaT= int(currentEpoch) - int(mTime)
    print "Synchronizing at ", datetime.datetime.utcnow().isoformat()
    #print currentEpoch, deltaT, mTime
    if deltaT <  time_in_past: 
        #Retrieve Data and send to public
        retrieve_data(path2pub, d)
        #Retrieve Data and send to Thredds
        retrieve_data(path2thredds, d)
    else:
        print "Everything is up to date"
  
if __name__ == "__main__":
    main()

