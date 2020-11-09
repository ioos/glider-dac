#!/usr/bin/env python
'''
This script alerts ERDDAP to recently updated delayed mode datasets
'''
import argparse
import logging
import os
import redis
import sys
from datetime import datetime, timezone, timedelta
from glider_dac import app, db

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s | %(levelname)s]  %(message)s'
)
logger = logging.getLogger(__name__)

# Connect to redis to keep track of the last time this script ran
redis_key = 'sync_erddap_datasets_last_run'
redis_host = app.config.get('REDIS_HOST', 'redis')
redis_port = app.config.get('REDIS_PORT', 6379)
redis_db = app.config.get('REDIS_DB', 0)
_redis = redis.Redis(
    host=redis_host,
    port=redis_port,
    db=redis_db
)


def main(args):
    '''
    This script loops through deployments checks for new data
    and touches the flag file for ERDDAP to pick it up

    TODO: Make this process event driven rather than reading the JSON
    files for every deployment each time.
    '''
    acquire_lock(args.lock_file)
    try:
        if args.deployment is not None:
            deployments = [args.deployment]
        else:
            deployments = get_delayed_mode_deployments(args.force)
            # Set the timestamp of this run in redis
            dt_now = datetime.now(tz=timezone.utc)
            _redis.set(redis_key, int(dt_now.timestamp()))

        if len(deployments) == 0:
            logger.info('No recently updated delayed mode datasets')
            return 0

        logger.info( "Processing the following deployments")
        for deployment in deployments:
            logger.info( " - %s", deployment)
            sync_deployment(deployment)

    finally:
        release_lock(args.lock_file)


def sync_deployment(deployment):
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
        logger.info("Touching flag file at %s", full_path)
        # technically could async this as it's I/O, but touching a file is pretty
        # unlikely to be a bottleneck
        with open(full_path, 'w') as f:
            pass  # Causes file creation (touch)

    logger.info( "--------------------------------------------------------------------------------")
    logger.info( "   Processing %s", deployment)
    logger.info( "--------------------------------------------------------------------------------")
    logger.info( "Synchronizing at %s", datetime.utcnow().isoformat())
    deployment_name = deployment.split('/')[-1]

    touch_erddap(deployment_name, app.config["flags_private"])


def get_delayed_mode_deployments(force=False):
    """
    Returns a list of the paths of delayed mode deployments to process.
    Filters deployments by ones updated since the last time this script ran,
    with a default or fallback to 24 hrs previously
    """
    query = {}
    query['delayed_mode'] = True  # Only return delayed mode datasets
    if not force:
        # Get datasets that have been updated since the last time this script ran
        try:
            dt_yesterday = datetime.now(tz=timezone.utc) - timedelta(days=1)
            last_run_ts = _redis.get(redis_key) or dt_yesterday.timestamp()
            last_run = datetime.utcfromtimestamp(int(last_run_ts))
            query['updated'] = {'$gte': last_run}
        except Exception:
            logger.error("Error: Parsing last run from redis. Processing Datasets from last 24 hrs")
            query['updated'] = {'$gte': dt_yesterday}

    deployments = db.Deployment.find(query)

    return [d.deployment_dir for d in deployments]


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
    parser.add_argument('-l', '--lock-file', default='/tmp/sync_erddap_datasets.lock', help='Lockfile to synchronize processes')
    parser.add_argument('-f', '--force', action="store_true", help="Force the processing of all datasets")
    parser.add_argument('-d', '--deployment', help="Manually load a specific deployment")
    parser.add_argument('-v', '--verbose', action="store_true", help="Sets log level to debug")
    args = parser.parse_args()
    with app.app_context():
        sys.exit(main(args))
