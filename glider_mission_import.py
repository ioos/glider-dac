#!/usr/bin/env python

"""
One-off script to update from filesystem based system to MongoDB based system.
"""
import os
import os.path
import argparse
from datetime import datetime

from glider_mission import app, db

users = ['rutgers']

def main(base):
    with app.app_context():
        for uname in users:
            u = db.User.find_one({'username':uname})
            assert u

            fullpath = os.path.join(base, uname, 'upload')

            for f in os.listdir(fullpath):
                if not os.path.isdir(os.path.join(fullpath, f)):
                    continue

                print "Mission", f

                mission = db.Mission.find_one({'name':f})

                if mission:
                    print "Found: updating timestamp"
                    mission.updated = datetime.utcfromtimestamp(os.path.getmtime(os.path.join(fullpath, f)))
                    mission.save()
                else:
                    print "Not Found: creating"
                    mission = db.Mission()
                    mission.name = unicode(f)
                    mission.user_id = u._id
                    mission.mission_dir = unicode(os.path.join(fullpath, f))

                    mission.completed = os.path.exists(os.path.join(fullpath, f, 'completed.txt'))

                    wmoid_file = os.path.join(fullpath, f, 'wmoid.txt')
                    if os.path.exists(wmoid_file):
                        with open(wmoid_file) as wf:
                            mission.wmo_id = unicode(wf.readline().strip())

                    mission.save()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('basedir',
                        default=os.environ.get('DATA_ROOT', '.'),
                        nargs='?')

    args = parser.parse_args()

    base = os.path.realpath(args.basedir)
    main(base)

