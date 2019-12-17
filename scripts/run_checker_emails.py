#!/usr/bin/env python
# -*- coding utf-8 -*-

from compliance_checker.suite import CheckSuite
from compliance_checker.runner import ComplianceChecker
import tempfile
import glob
import sys
import os
import json
from itertools import chain, combinations
import argparse
from collections import OrderedDict, defaultdict
from more_itertools import consecutive_groups
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

def pset_len(set_list, r):
  return [(r, set.intersection(*i)) for i in combinations(set_list, r)]

def main():
    args = parser.parse_args()
    cs = CheckSuite()
    cs.load_all_available_checkers()
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
        agg_pipeline = [{"$match": q_dict},
                        {"$group": {"_id": "$user_id",
                           "deployments": {"$push":
                                {"_id": "$_id",
                                 "name": "$name",
                                 "deployment_dir": "$deployment_dir"} } }
                        }]
        # if force is enabled, re-check the datasets no matter what
        for res in db.deployments.aggregate(agg_pipeline)['result']:
            user = db.users.find_one(res["_id"])
            all_messages = []
            failing_deployments = []
            for dep in res['deployments']:
                try:
                    dep_passed, dep_messages = process_deployment(dep)
                    all_messages.append(dep_messages)
                    if not dep_passed:
                        failing_deployments.append(dep)
                except Exception as e:
                    root_logger.exception(
                        "Exception occurred while processing deployment {}".format(dep['name']))
                    text_body = ''
            send_deployment_cchecker_email(user, failing_deployments,
                                           "\n".join(all_messages))

def process_deployment(dep):
    os.chdir(os.path.join("/data/data/priv_erddap",
                          dep['deployment_dir']))
    deployment_issues = "Deployment {}".format(os.path.basename(dep['name']))
    groups = OrderedDict()

    for file_number, (fname, res) in enumerate(file_loop()):
        # TODO: memoize call?
        if len(res) == 0:
            continue
        else:
            if res not in groups:
                groups[res] = []

            groups[res].append((file_number, fname))

    all_keys = set.union(*[set(kg) for kg in groups.keys()])
    prev_keys = set()
    messages = []
    while prev_keys != all_keys:
        prev_keys, error_text = parse_issues(groups, prev_keys)
        messages.append(error_text)
    # can we work with the raw object instead of finding via a dict
    dep_obj = db.Deployment.find_one({'_id': dep['_id']})
    compliance_passed = len(messages) == 0
    if compliance_passed:
        final_message = "All files passed compliance check on glider deployment {}".format(dep['name'])
    else:
        final_message = ("Deployment {} has issues:\n".format(dep['name']) +
                         "\n".join(messages))
    dep_obj["compliance_check_passed"] = compliance_passed
    dep_obj.save()
    return compliance_passed, final_message

# intersection of all issues
def parse_issues(groups, prev_issues=None):
    """
    Parses the issues, exlcuding any that weren't previously present
    """
    if prev_issues is None:
	prev_issues = set()
    leftover_issues = [set(k) - prev_issues for k in groups.keys()
		       if len(set(k) - prev_issues) > 0]
    core_issues = [set.intersection(*[set(k) for k in leftover_issues])]
    # if the intersection is zero length, we've hit the end of shared issues
    if len(core_issues[0]) == 0:
	if len(leftover_issues) > 2:
	    tiebreak_issues = [i for i in
				  chain.from_iterable(pset_len(leftover_issues, r)
				  for r in range(2, len(leftover_issues)))
				  if len(i[1]) > 0]
            if len(tiebreak_issues) == 0:
               issues = leftover_issues
            else:
		issues = [max(tiebreak_issues,
			     key=lambda tup: (tup[0], len(tup[1])))[1]]
	else:
	    issues = leftover_issues
    else:
	issues = core_issues

    for issue_set in issues:
        affected_files = [(file_ct, name) for errors, file_info in
			  groups.items() for file_ct, name in file_info if
			  issue_set.issubset(errors)]
	contiguous_files = [list(g) for g in consecutive_groups(affected_files, lambda x: x[0])]

	fname_message = ', '.join("{} to {}".format(l[0][1],
						    l[-1][1])
				  if len(l) > 1 else l[0][1] for
				  l in contiguous_files)

	error_str = "\n".join([' * {}'.format(i) for i
			       in sorted(issue_set)])
    return (prev_issues | set.union(*issues),
            "{}\n{}".format(fname_message, error_str))


def file_loop(filepath=None):
    """
    Gets subset of error messages

    """
    # TODO: consider parallelizing this loop for speed gains
    if filepath is None:
        glob_path = '*.nc'
    else:
        glob_path = os.path.join(filepath, '*.nc')
    for nc_filename in sorted(glob.iglob(glob_path)):
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
        all_errs = tuple(er_msg for er in ers['gliderdac']['high_priorities'] for
                         er_msg in er['msgs'] if er['value'][0] < er['value'][1])

        yield (nc_filename, all_errs)


if __name__ == '__main__':
    main()
