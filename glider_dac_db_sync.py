#!/usr/bin/env python

import time
import os.path
import os
import argparse
import logging
import smtplib
import subprocess

from datetime import datetime

from watchdog.events import (FileSystemEventHandler, DirCreatedEvent,
                             DirDeletedEvent, FileCreatedEvent, FileMovedEvent)
from watchdog.observers import Observer

from glider_dac import app, db

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]  %(message)s')
logger = logging.getLogger(__name__)

class HandleDeploymentDB(FileSystemEventHandler):
    def __init__(self, base):
        self.base     = base

    def file_moved_or_created(self, event):
        logger.info('%s %s', self.base, event.src_path)
        if self.base not in event.src_path:
            return

        rel_path = os.path.relpath(event.src_path, self.base)
        path_parts = os.path.split(rel_path)
        logger.info("%s %s", type(event), path_parts)

        # ignore if a dotfile
        if path_parts[1].startswith('.'):
            return


        with app.app_context():
            deployment = db.Deployment.find_one({'deployment_dir' : path_parts[0]})
            if deployment is None:
                logger.error("Cannot find deployment for %s", path_parts[0])
                return

            if path_parts[-1] == "wmoid.txt":
                rel_path = os.path.relpath(event.src_path, self.base)
                logger.info("New wmoid.txt in %s", rel_path)
                if deployment.wmo_id:
                    logger.info("Deployment already has wmoid %s.  Updating value with new file.", deployment.wmo_id)
                with open(event.src_path) as wf:
                    deployment.wmo_id = unicode(wf.readline().strip())
                deployment.save()
                logger.info("Updated deployment %s", path_parts[0])
            else:
                # Always save the Deployment when a new dive file is added
                # so a checksum is calculated and a new deployment.json file
                # is created
                fname, ext = os.path.splitext(path_parts[-1])
                if ext not in ['.md5', '.txt']:
                    deployment.save()
                    logger.info("Updated deployment %s", path_parts[0])

    def on_moved(self, event):
        if isinstance(event, FileMovedEvent):
            self.file_moved_or_created(event)


    def on_created(self, event):
        if isinstance(event, DirCreatedEvent):

            if self.base not in event.src_path:
                return

            rel_path = os.path.relpath(event.src_path, self.base)

            # we only care about this path if it's under a user dir
            # user/upload/deployment-name
            path_parts = rel_path.split(os.sep)

            if len(path_parts) != 3:
                return

            logger.info("New deployment directory: %s", rel_path)

            with app.app_context():
                deployment = db.Deployment.find_one({'deployment_dir':event.src_path})
                if deployment is None:
                    deployment             = db.Deployment()

                    usr = db.User.find_one( { 'username' : unicode(path_parts[0]) } )
                    if hasattr(usr, '_id'):
                        deployment.user_id     = usr._id
                        deployment.name        = unicode(path_parts[2])
                        deployment.deployment_dir = unicode(event.src_path)
                        deployment.updated     = datetime.utcnow()
                        deployment.save()

        elif isinstance(event, FileCreatedEvent):
            self.file_moved_or_created(event)

    def on_deleted(self, event):
        if isinstance(event, DirDeletedEvent):
            if self.base not in event.src_path:
                return

            rel_path = os.path.relpath(event.src_path, self.base)

            # we only care about this path if it's under a user dir
            # user/upload/deployment-name
            path_parts = rel_path.split(os.sep)

            if len(path_parts) != 3:
                return

            logger.info("Removed deployment directory: %s", rel_path)

            with app.app_context():
                deployment = db.Deployment.find_one({'deployment_dir':event.src_path})
                if deployment:
                    deployment.delete()

def main(handler):
    observer = Observer()
    observer.schedule(handler, path=handler.base, recursive=True)
    observer.start()

    logger.info("Watching user directories in %s", handler.base)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('basedir',
                        default=os.environ.get('DATA_ROOT', '.'),
                        nargs='?')

    args = parser.parse_args()

    base = os.path.realpath(args.basedir)
    main(HandleDeploymentDB(base))

