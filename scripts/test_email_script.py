#!/usr/bin/env python
# -*- coding utf-8 -*-

from compliance_checker.suite import CheckSuite
from compliance_checker.runner import ComplianceChecker
import tempfile
import glob
import sys
import os
import json
from itertools import groupby
import argparse
from glider_dac import app, db
from glider_dac.glider_emails import send_deployment_cchecker_email
import logging


parser = argparse.ArgumentParser()
arg_group = parser.add_mutually_exclusive_group()
arg_group.add_argument('-t', dest='data_type', choices=['realtime', 'delayed'])
arg_group.add_argument('-d', dest='deployment_dir', type=str)

parser.add_argument('-c', '--completed', dest='completed',
                       action='store_true')
# TODO: maybe don't use on deployment, as it should already be explicit whether
#       desired or not?
parser.add_argument('-f', '--force', dest='force', action='store_true')

parser.set_defaults(completed=False)
parser.set_defaults(force=False)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.INFO)
root_logger.addHandler(handler)


def main():
    args = parser.parse_args()
    cs = CheckSuite()
    cs.load_all_available_checkers()
    groups = []
    uniquekeys = []
    with app.app_context():
        if args.data_type is not None:
            is_delayed_mode = args.data_type == 'delayed'
            if is_delayed_mode:
                q_dict = {"delayed_mode": True,
                          "completed": args.completed}
            else:
                q_dict = {"$or": [{"delayed_mode": False},
                                  {"delayed_mode": {"$exists": False}}],
                          "completed": args.completed}

            if not args.force:
                q_dict["compliance_check_passed"] = {"$ne": True}

        # a particular deployment has been specified
        else:
            q_dict = {"deployment_dir": args.deployment_dir}
        # if force is enabled, re-check the datasets no matter what
        for dep in db.Deployment.find(q_dict):
            deployment_issues = "Deployment {}".format(os.path.basename(dep.name))

            # TODO: remove hardcoding
            dep_dir = os.path.join("/data/data/priv_erddap", dep.deployment_dir)
        
            try:
                for k, g in groupby(file_loop(dep_dir), lambda x: x[1]):
                    groups.append(list(g))
                    uniquekeys.append(k)
                for group in groups:
                    deployment_issues += "\nIssues for files {} through {}:".format(os.path.basename(group[0][0]),
                                             os.path.basename(group[-1][0]))
                    for issue in group[0][1]:
                        deployment_issues += "\n\t- {}".format(issue)
            except Exception as e:
                root_logger.exception()
                continue


            # is there a better way to fetch these individual objects?
            # db.Deployment.find() returns a cursor which returns dict objects
            dep_obj = db.Deployment.find_one({'_id': dep['_id']})

            # check only passes if there are no errors
            dep_obj["compliance_check_passed"] = len(group[0][1]) == 0
            dep_obj.save()
            send_deployment_cchecker_email(dep, deployment_issues)
            



def file_loop(filepath):
    """
    Gets subset of error messages
    
    """
    # TODO: consider parallelizing this loop for speed gains
    for nc_filename in sorted(glob.iglob(os.path.join(filepath, '*.nc'))):
        root_logger.info("Processing {}".format(nc_filename))
        # TODO: would be better if we didn't have to write to a temp file
        # and instead could just
        outhandle, outfile = tempfile.mkstemp()
        try:
            ComplianceChecker.run_checker(ds_loc=nc_filename,
                                          checker_names=['gliderdac'], verbose=True,
                                          criteria='normal', output_format='json',
                                          output_filename=outfile)

            with open(outfile, 'rt') as f:
                ers = json.loads(f.read())
        finally:
            # fix this?
            os.close(outhandle)
            if os.path.isfile(outfile):
                os.remove(outfile)

        # TODO: consider rewriting this when Glider DAC compliance checker
        # priorities are refactored

        # BWA: change over to high priority messages w/ cc-plugin-glider
        #      2.0.0 release instead of string matching
        all_errs = [er_msg for er in ers['gliderdac']['high_priorities'] for
                    er_msg in er['msgs'] if er['value'][0] < er['value'][1]]

        yield (nc_filename, all_errs)


if __name__ == '__main__':
    main()
