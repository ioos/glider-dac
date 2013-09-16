#!/usr/bin/env python

"""
A utility for dealing with BerkeleyDB user/pass files for Glider DAC.

See glider_mission.bdb.UserDB for more information.

Usage:
    ./usertool.py mydb.db init
    ./usertool.py mydb.db set testuser
        Password:
    ./usertool.py mydb.db list
        testuser
    ./usertool.py mydb.db check testuser
        Password:
        Success
"""

import os.path
import sys
import argparse
import getpass
from glider_util.bdb import UserDB

class UserAction(argparse.Action):
    def __call__(self, parser, args, values, option = None):
        if args.op in ['set', 'check'] and not values:
            parser.error("You must specify a user for the '%s' operation" % args.op)

        args.user=values

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('db_file', help='Path to the BDB user file')
    parser.add_argument('op', choices=['set', 'list', 'check', 'init'], help='"set" a user\'s password, "check" a user\'s password, "list" all known users')
    parser.add_argument('user', nargs='?', action=UserAction, help='Username')

    args = parser.parse_args()

    if not os.path.exists(args.db_file) and not args.op == "init":
        raise StandardError("File %s does not exist. Use %s %s 'init' if you want to create it" % (args.db_file, sys.argv[0], args.db_file))

    u = UserDB(args.db_file)

    if args.op == 'set':
        pw = getpass.getpass()

        u.set(args.user, pw)
    elif args.op == 'check':
        pw = getpass.getpass()

        cv = u.check(args.user, pw)
        if cv:
            print "Success"
        else:
            print "Failure"
            sys.exit(1)

    elif args.op == 'list':
        print "\n".join(u.list_users())

    elif args.op == 'init':
        u.init_db(args.db_file)


