import os
from flask_mail import Message
from flask import render_template
from glider_dac.models.deployment import Deployment
#from glider_dac import app, mail, db
#from glider_dac import mail, db
from flask import current_app
from datetime import datetime
from compliance_checker.suite import CheckSuite
from compliance_checker.runner import ComplianceChecker
from urllib.parse import urljoin
from sqlalchemy import func
import tempfile
import glob
import sys
import os
import json
import argparse
from collections import OrderedDict
import logging
import functools


root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.INFO)
root_logger.addHandler(handler)


def email_exception_logging_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            root_logger.exception("Exception occurred while attempting to send "
                                  "email: ")
    return wrapper

@email_exception_logging_wrapper
def send_registration_email(username, deployment):
    if not app.config.get('MAIL_ENABLED', False): # Mail is disabled
        app.logger.info("Email is disabled")
        return
    # sender comes from MAIL_DEFAULT_SENDER in env
    app.logger.info("Sending email about new deployment to %s", app.config.get('MAIL_DEFAULT_TO'))
    subject        = "New Glider Deployment - %s" % deployment.name
    recipients     = [app.config.get('MAIL_DEFAULT_TO')]
    cc_recipients  = []
    if app.config.get('MAIL_DEFAULT_LIST') is not None:
        cc_recipients.append(app.config.get('MAIL_DEFAULT_LIST'))

    msg            = Message(subject, recipients=recipients, cc=cc_recipients)
    msg.body       = render_template(
                        'deployment_registration.txt',
                        deployment=deployment,
                        username=username,
                        thredds_url=get_thredds_catalog_url(),
                        erddap_url=get_erddap_catalog_url())

    current_app.mail.send(msg)

@email_exception_logging_wrapper
def send_deployment_cchecker_email(user, failing_deployments, attachment_msgs):
    if not app.config.get('MAIL_ENABLED', False): # Mail is disabled
        app.logger.info("Email is disabled")
        return
    # sender comes from MAIL_DEFAULT_SENDER in env

    app.logger.info("Sending email about deployment compliance checker to {}".format(user['username']))
    subject        = "Glider DAC Compliance Check on Deployments for user %s" % user['username']
    recipients     = [user['email']] #app.config.get('MAIL_DEFAULT_TO')]
    msg            = Message(subject, recipients=recipients)
    if len(failing_deployments) > 0:
        message = ("The following glider deployments failed compliance check:"
                   "\n{}\n\nPlease see attached file for more details. "
                   "Valid CF standard names are required for NCEI archival."
                   .format("\n".join(d['name'] for d in failing_deployments)))
        date_str_today = datetime.today().strftime("%Y-%m-%d")
        attachment_filename = "failing_glider_md_{}".format(date_str_today)
        msg.attach(attachment_filename, 'text/plain', data=attachment_msgs)
    else:
        return
    msg.body       = message

    current_app.mail.send(msg)

def get_thredds_catalog_url():
    args = {
        'host' : app.config['THREDDS']
    }
    url = 'http://%(host)s/thredds/catalog.xml' % args
    return url

def get_erddap_catalog_url():
    args = {
        'host' : app.config['PUBLIC_ERDDAP']
    }
    url = 'http://%(host)s/erddap/metadata/iso19115/xml/' % args
    return url

def glider_deployment_check(data_type=None, completed=True, force=False,
                            deployment_dir=None, username=None):
    """
    """
    # TODO: move this functionality to another module as compliance checks
    #       no longer send emails.
    cs = CheckSuite()
    cs.load_all_available_checkers()
    query = Deployment.query
    with app.app_context():
        if data_type is not None:
            query = query.filter(Deployment.completed==completed,
                                            func.coalesce(Deployment.delayed_mode,
                                                        False) == is_delayed_mode)
            # TODO: force not null constraints in model on this field
            if not force:
                query = query.filter(compliance_check_passed != True)

        if username:
            query = query.filter_by(username=username)
        # a particular deployment has been specified







        elif deployment_dir:
            query = query.filter_by(deployment_dir=deployment_dir)

    for deployment in query.all():
        user = deployment.username
        user_errors.setdefault(user, {"messages": [], "failed_deployments": []})

        try:
            dep_passed, dep_messages = process_deployment(deployment)
            if not dep_passed:
                user_errors[user]["failed_deployments"].append(deployment.name)
            user_errors[user]["messages"].extend(dep_messages)
        except Exception as e:
            root_logger.exception("Exception occurred while processing deployment {}".format(deployment.name))

        # TODO: Allow for disabling of sending compliance checker emails
        for username, results_dict in user_errors.items():
            send_deployment_cchecker_email(username,
                                           results_dict["failed_deployments"],
                                           "\n".join(results_dict["messages"]))



def process_deployment(dep):
    deployment_issues = "Deployment {}".format(os.path.basename(dep.name))
    groups = OrderedDict()
    erddap_fmt_string = "erddap/tabledap/{}.nc?&time%3Emax(time)-1%20day"
    base_url = app.config["PRIVATE_ERDDAP"]
    # FIXME: determine a more robust way of getting scheme
    if not base_url.startswith("http"):
        base_url = "http://{}".format(base_url)
    url_path = "/".join([base_url,
                         erddap_fmt_string.format(dep.name)])
    # TODO: would be better if we didn't have to write to a temp file
    outhandle, outfile = tempfile.mkstemp()
    failures, _ = ComplianceChecker.run_checker(ds_loc=url_path,
                                  checker_names=['gliderdac'], verbose=True,
                                  criteria='lenient', output_format='json',
                                  output_filename=outfile)
    with open(outfile, 'r') as f:
        errs = json.load(f)["gliderdac"]

    compliance_passed = errs['scored_points'] == errs['possible_points']

    dep.compliance_check_passed = compliance_passed
    standard_name_errs = []
    if compliance_passed:
        final_message = "All files passed compliance check on glider deployment {}".format(dep.name)
    else:
        error_list = [err_msg for err_severity in ("high_priorities",
            "medium_priorities", "low_priorities") for err_section in
            errs[err_severity] for err_msg in err_section["msgs"]]
        dep.compliance_check_report = errs

        for err in errs["high_priorities"]:
            if err["name"] == "Standard Names":
                standard_name_errs.extend(err["msgs"])

        if not standard_name_errs:
            final_message = "All files passed compliance check on glider deployment {}".format(dep.name)
        else:
            root_logger.info(standard_name_errs)
            final_message = ("Deployment {} has issues:\n{}".format(dep.name,
                             "\n".join(standard_name_errs)))

    db.session.commit()
    return final_message.startswith("All files passed"), final_message
