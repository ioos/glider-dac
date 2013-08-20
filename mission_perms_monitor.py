#!/usr/bin/env python

"""
Mission dir perms watcher/fixer.

This has to be run as root.

It monitors the mission dirs created in $DATA_ROOT/<user>/upload and changes their ownership
to the user. This is to repair the web New Mission button's creation.
"""

import time
import os.path
import os
import argparse
import logging
import pwd
import grp

from watchdog.events import FileSystemEventHandler, DirCreatedEvent, FileModifiedEvent, DirModifiedEvent
from watchdog.observers import Observer

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]  %(message)s')
logger = logging.getLogger(__name__)

class HandleMissionDir(FileSystemEventHandler):
    def __init__(self, base):
        self.base = base

    def _fix_perms(self, path, rel_path, username):
        logger.info("New path: %s", rel_path)

        # lookup username's uid/gid
        uid = pwd.getpwnam(username).pw_uid
        gid = grp.getgrnam('sftponly').gr_gid

        logger.info("Changing %s to owner %s (%s)/group sftponly (%s)", rel_path, username, uid, gid)
        os.chown(path, uid, gid)

    def on_created(self, event):
        if self.base not in event.src_path:
            return

        rel_path = os.path.relpath(event.src_path, self.base)

        if isinstance(event, DirCreatedEvent):

            # we only care about this path if it's under a user dir
            # user/upload/mission-name
            path_parts = rel_path.split(os.sep)

            if len(path_parts) != 3:
                return

        else:

            # should resemble user/upload/mission-name/wmo-file
            path_parts = rel_path.split(os.sep)
            if len(path_parts) != 4:
                return

            # only looking for wmoid.txt named files
            if path_parts[-1] != "wmoid.txt":
                return

        # allow a slight delay so if the web app wants to create wmoid.txt it still can
        time.sleep(5)

        self._fix_perms(event.src_path, rel_path, path_parts[0])

        # Touch src directory so on_modified will get called
        os.utime(event.src_path, None)

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
    main(HandleMissionDir(base))

