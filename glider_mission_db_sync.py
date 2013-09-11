#!/usr/bin/env python

import time
import os.path
import os
import argparse
import logging
import smtplib
import subprocess

from watchdog.events import FileSystemEventHandler, DirCreatedEvent, DirDeletedEvent
from watchdog.observers import Observer

from glider_mission import app, db

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]  %(message)s')
logger = logging.getLogger(__name__)

class HandleMissionDB(FileSystemEventHandler):
    def __init__(self, base):
        self.base     = base

    def on_created(self, event):
        if isinstance(event, DirCreatedEvent):

            if self.base not in event.src_path:
                return

            rel_path = os.path.relpath(event.src_path, self.base)

            # we only care about this path if it's under a user dir
            # user/upload/mission-name
            path_parts = rel_path.split(os.sep)

            if len(path_parts) != 3:
                return

            logger.info("New mission directory: %s", rel_path)

            with app.app_context():
                mission = db.Mission.find_one({'mission_dir':event.src_path})
                if mission is None:
                    mission             = db.Mission()
                    mission.name        = unicode(path_parts[2])
                    mission.user        = unicode(path_parts[0])
                    mission.mission_dir = unicode(event.src_path)
                    mission.save()

    def on_deleted(self, event):
        if isinstance(event, DirDeletedEvent):
            if self.base not in event.src_path:
                return

            rel_path = os.path.relpath(event.src_path, self.base)

            # we only care about this path if it's under a user dir
            # user/upload/mission-name
            path_parts = rel_path.split(os.sep)

            if len(path_parts) != 3:
                return

            logger.info("Removed mission directory: %s", rel_path)

            with app.app_context():
                mission = db.Mission.find_one({'mission_dir':event.src_path})
                if mission:
                    mission.delete()


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
    main(HandleMissionDB(base))

