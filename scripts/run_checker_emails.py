#!/usr/bin/env python
# -*- coding utf-8 -*-
import argparse
from glider_dac.glider_emails import glider_deployment_check

def main():
    parser = argparse.ArgumentParser()
    arg_group = parser.add_mutually_exclusive_group()
    arg_group.add_argument('-t', dest='data_type', choices=['realtime', 'delayed'])
    arg_group.add_argument('-d', dest='deployment_dir', type=str)
    arg_group.add_argument('-u', dest='username', type=str)

    parser.add_argument('-c', '--completed', dest='completed',
                        action='store_true')
# TODO: maybe don't use on deployment, as it should already be explicit whether
#       desired or not?
    parser.add_argument('-f', '--force', dest='force', action='store_true')

    parser.set_defaults(completed=False)
    parser.set_defaults(force=False)
    args = parser.parse_args()

    glider_deployment_check(args.data_type, args.completed, args.force,
                            args.deployment_dir, args.username)

if __name__ == '__main__':
    main()
