from rq import Queue, Connection
from redis import Redis, StrictRedis
from glider_dac import redis_pool
from rq_scheduler import Scheduler
from scripts import (replicatePrivateErddapDeployments, download_waf)
import argparse
from datetime import datetime

connection = StrictRedis(connection_pool=redis_pool)
scheduler = Scheduler(connection=connection)

# simulate argparse call

scheduler.cron("15 */2 * * *",
               replicatePrivateErddapDeployments.main,
               args=[argparse.Namespace(lock_file="/tmp/replicate.lock",
                     force=False, deployment=None)])

scheduler.cron("0 * * * *", download_waf.main,
               args=[argparse.Namespace(destination="/tmp/waf",
                                        erddap="https://data.ioos.us/gliders/erddap",
                                        suffix=".erddap")])

scheduler.cron("0 * * * *", download_waf.main,
               args=[argparse.Namespace(destination="/tmp/waf",
                                        thredds="https://data.ioos.us/thredds/catalog.xml",
                                        suffix=".thredds")])
