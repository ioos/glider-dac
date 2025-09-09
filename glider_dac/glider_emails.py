import os
from flask_mail import Message
from flask import render_template, url_for
from glider_dac import app, mail, db
from datetime import datetime, timedelta
from compliance_checker.suite import CheckSuite
from compliance_checker.runner import ComplianceChecker
from urllib.parse import urljoin
import pymongo
import tempfile
import glob
import sys
import os
import json
import argparse
from collections import OrderedDict
import logging


root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.INFO)
root_logger.addHandler(handler)


def send_email_wrapper(message):
    """
    Email sending function with exceptions to catch and log exceptions
    """
    try:
        mail.send(message)
    except:
        app.logger.exception("Exception occurred while attempting to send "
                             "email: ")


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

    send_email_wrapper(msg)

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

    send_email_wrapper(msg)

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
    with app.app_context():
        if data_type is not None:
            is_delayed_mode = data_type == 'delayed'
            if is_delayed_mode:
                q_dict = {"delayed_mode": True,
                          "completed": completed}
            else:
                q_dict = {"$or": [{"delayed_mode": False},
                                  {"delayed_mode": {"$exists": False}}],
                          "completed": completed}

            if not force:
                q_dict["compliance_check_passed"] = {"$ne": True}

        # TODO: combine username/deployment cases?
        if username:
            q_dict = {"username": username}
        # a particular deployment has been specified
        elif deployment_dir:
            q_dict = {"deployment_dir": deployment_dir}
        else:
            q_dict = {}

        agg_pipeline = [{"$match": q_dict},
                        {"$group": {"_id": "$user_id",
                           "deployments": {"$push":
                                {"_id": "$_id",
                                 "name": "$name",
                                 "deployment_dir": "$deployment_dir"} } }
                        }]
        # if force is enabled, re-check the datasets no matter what

        # is this syntax still used?  if the first fn call fails, use the
        # second set of results
        try:
            agg_result_set = db.deployments.aggregate(agg_pipeline)['result']
        except:
            agg_result_set = db.deployments.aggregate(agg_pipeline, cursor={})
        for res in agg_result_set:
            user = db.users.find_one(res["_id"])
            all_messages = []
            failing_deployments = []
            for dep in res['deployments']:
                root_logger.info("Running compliance check on glider "
                                 "deployment: {}".format(dep))
                try:
                    dep_passed, dep_messages = process_deployment(dep)
                    all_messages.append(dep_messages)
                    if not dep_passed:
                        failing_deployments.append(dep)
                except Exception as e:
                    root_logger.exception(
                        "Exception occurred while processing deployment {}".format(dep['name']))
                    text_body = ''
        # disable email for time being
        #send_deployment_cchecker_email(user, failing_deployments,
        #                               "\n".join(all_messages))

def process_deployment(dep):
    deployment_issues = "Deployment {}".format(os.path.basename(dep['name']))
    groups = OrderedDict()
    erddap_fmt_string = "erddap/tabledap/{}.nc?&time%3Emax(time)-1%20day"
    base_url = app.config["PRIVATE_ERDDAP"]
    # FIXME: determine a more robust way of getting scheme
    if not base_url.startswith("http"):
        base_url = "http://{}".format(base_url)
    url_path = "/".join([base_url,
                         erddap_fmt_string.format(dep["name"])])
    # TODO: would be better if we didn't have to write to a temp file
    outhandle, outfile = tempfile.mkstemp()
    try:
        failures, _ = ComplianceChecker.run_checker(ds_loc=url_path,
                                      checker_names=['gliderdac'], verbose=True,
                                      criteria='lenient', output_format='json',
                                      output_filename=outfile)
        with open(outfile, 'r') as f:
            errs = json.load(f)["gliderdac"]

        compliance_passed = errs['scored_points'] == errs['possible_points']
    except OSError:
        root_logger.exception("Potentially failed to open netCDF file:")
        compliance_passed = False

    update_fields = {"compliance_check_passed": compliance_passed}
    standard_name_errs = []
    if compliance_passed:
        final_message = "All files passed compliance check on glider deployment {}".format(dep['name'])
    else:
        error_list = [err_msg for err_severity in ("high_priorities",
                      "medium_priorities", "low_priorities") for err_section in
                      errs[err_severity] for err_msg in err_section["msgs"]]
        update_fields["compliance_check_report"] = errs

        for err in errs["high_priorities"]:
            if err["name"] == "Standard Names":
                standard_name_errs.extend(err["msgs"])

        if not standard_name_errs:
            final_message = "All files passed compliance check on glider deployment {}".format(dep['name'])
        else:
            root_logger.info(standard_name_errs)
            final_message = ("Deployment {} has issues:\n{}".format(dep['name'],
                             "\n".join(standard_name_errs)))

    # Set fields.  Don't use upsert as deployment ought to exist prior to write.
    db.deployments.update({"_id": dep["_id"]}, {"$set": update_fields})
    return final_message.startswith("All files passed"), final_message

def notify_incomplete_deployments(username):
    # Calculate the date two weeks ago
    dt_run = datetime.now()
    soft_time_limit = dt_run - timedelta(days=30)
    hard_time_limit = dt_run - timedelta(days=90)

    # Query for deployments that are not completed, last updated more than two weeks ago, and match the username
    incomplete_deployments = db.Deployment.find({
        'completed': False,
        'updated': {'$lt': soft_time_limit},
        'username': username  # Filter by username
    }).sort('updated', pymongo.ASCENDING)

    # Convert the cursor to a list
    deployments = list(incomplete_deployments)

    # Check if there are any deployments to notify about
    if not deployments:
        return

    # Prepare email content
    subject = f"Reminder: Incomplete Deployments for {username}"

    # Start building the HTML table




    body = f"""
    <html>
    <body>
    <p>Hello,</p>

    <p>This is an automated notification for user {username} regarding your glider deployment(s) on the IOOS Glider DAC.
    Our records indicate that the following deployments have had no activity for more than 30 days. To maintain accurate records, we request that providers mark completed deployments as "complete" in the system.</p>

    <h3><em>What happens next?</em></h3>

    <p>After 90 days of total inactivity, this deployment will be automatically marked as "complete."</p>

    <p>
    If your deployments are still active, please ignore this message as your next data submission will reset the timer.
    If you wish to keep the deployment open but inactive, or have any questions, please contact us at <a href="mailto:glider.dac.support@noaa.gov">glider.dac.support@noaa.gov</a>
    Please visit our <a href="https://ioos.github.io/glider-dac/ngdac-netcdf-file-submission-process.html#dataset-archiving">documentation</a> for more information on marking deployments as complete and submitting data to the National Centers for Environmental Information (NCEI) for archiving.
    </p>

    <p>
    Thank you,
    The IOOS Glider DAC Team
    </p>

    <table border="1" style="border-collapse: collapse;">
        <tr>
            <th>Deployment Name</th>
            <th>Last Updated</th>
            <th>Older than 90 days, automatically marked as completed?</th>
        </tr>
    """

    for deployment in deployments:
        exceeds_hard_limit = False
        if deployment.updated <= hard_time_limit:
            exceeds_hard_limit = True
            deployment.completed = True
            deployment.save()
        # FIXME: url_for is repeated in views/deployment.py under show_deployment_no_username
        #        can't import due to circular imports -- consider moving to views instead
        body += f"""
            <tr>
                <td><a href={url_for('show_deployment', username=username, deployment_id=deployment._id)}>{deployment.name}</a></td>
                <td>{deployment.updated.strftime('%Y-%m-%d %H:%M:%S')}</td>
                <td>{"X" if exceeds_hard_limit else ""}</td>
            </tr>
        """

    body += """
        </table>
    </body>
    </html>
    """

    user_email = db.users.find_one({"username": username})["email"]
    msg = Message(subject, recipients=[user_email])
    msg.html = body

    send_email_wrapper(msg)
