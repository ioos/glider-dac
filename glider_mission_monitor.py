#!/usr/bin/env python

import time
import os.path
import os
import argparse
import logging
import subprocess

from watchdog.events import FileSystemEventHandler, DirCreatedEvent, FileModifiedEvent, DirModifiedEvent
from watchdog.observers import Observer

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]  %(message)s')
logger = logging.getLogger(__name__)

RSYNC_SSH_USER = os.environ.get('RSYNC_SSH_USER', 'gliderweb')
RSYNC_TO_HOST  = os.environ.get('RSYNC_TO_HOST', None)
RSYNC_TO_PATH  = os.environ.get('RSYNC_TO_PATH', '/data')

class HandleMission(FileSystemEventHandler):
    def __init__(self, base):
        self.base     = base

    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent):
            rel_path = os.path.relpath(event.src_path, self.base)
            path_parts = rel_path.split(os.sep)

            # expecting user/upload/mission-name/file
            if len(path_parts) != 4:
                return

            logger.info("File modified in watched dir (%s), rsyncing", rel_path)

            # rsync the containing directory
            src = os.path.split(event.src_path)[0]
            dest = os.path.join(RSYNC_TO_PATH, path_parts[0])    # username only from this path
            self._perform_rsync(src, dest)

        elif isinstance(event, DirModifiedEvent):
            rel_path = os.path.relpath(event.src_path, self.base)
            path_parts = rel_path.split(os.sep)

            # expecting user/upload/mission-name
            if len(path_parts) != 3:
                return

            logger.info("Directory modified (%s), rsyncing", rel_path)

            # rsync this directory
            src = event.src_path
            dest = os.path.join(RSYNC_TO_PATH, path_parts[0])    # username only from this path
            self._perform_rsync(src, dest)

    def _perform_rsync(self, src, dest):
        if RSYNC_TO_HOST is not None:
            dest = "%s:%s" % (RSYNC_TO_HOST, dest)

        args = ['rsync', '-r', '-a', '-v', '-e', 'ssh -l ' + RSYNC_SSH_USER, src, dest]
        logger.info("Spawning %s", " ".join(args))

        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        if len(stdout):
            logger.info(stdout)
        if len(stderr):
            logger.warn(stderr)

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
    main(HandleMission(base))

