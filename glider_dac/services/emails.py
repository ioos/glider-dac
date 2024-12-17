import os
from flask_mail import Message
from flask import render_template, current_app
from glider_dac import db
from glider_dac.models.deployment import Deployment
from datetime import datetime, timedelta
from compliance_checker.suite import CheckSuite
from compliance_checker.runner import ComplianceChecker
from urllib.parse import urljoin
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
        current_app.logger.exception("Exception occurred while attempting to send "
                             "email:")


def send_registration_email(username, deployment):
    if not current_app.config.get('MAIL_ENABLED', False): # Mail is disabled
        current_app.logger.info("Email is disabled")
        return
    # sender comes from MAIL_DEFAULT_SENDER in env
    current_app.logger.info("Sending email about new deployment to %s", current_app.config.get('MAIL_DEFAULT_TO'))
    subject        = "New Glider Deployment - %s" % deployment.name
    recipients     = [current_app.config.get('MAIL_DEFAULT_TO')]
    cc_recipients  = []
    if current_app.config.get('MAIL_DEFAULT_LIST') is not None:
        cc_recipients.current_append(current_app.config.get('MAIL_DEFAULT_LIST'))

    msg = Message(subject, recipients=recipients, cc=cc_recipients)
    msg.body = render_template(
                        'deployment_registration.txt',
                        deployment=deployment,
                        username=username,
                        thredds_url=get_thredds_catalog_url(),
                        erddap_url=get_erddap_catalog_url())

    send_email_wrapper(msg)

def send_deployment_cchecker_email(user, failing_deployments, attachment_msgs):
    if not current_app.config.get('MAIL_ENABLED', False): # Mail is disabled
        current_app.logger.info("Email is disabled")
        return
    # sender comes from MAIL_DEFAULT_SENDER in env

    current_app.logger.info("Sending email about deployment compliance checker to {}".format(user['username']))
    subject        = "Glider DAC Compliance Check on Deployments for user %s" % user['username']
    recipients     = [user['email']]
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

# TODO: move to utilities.py
def get_thredds_catalog_url():
    args = {
        'host' : current_app.config['THREDDS']
    }
    url = 'http://%(host)s/thredds/catalog.xml' % args
    return url

def get_erddap_catalog_url():
    args = {
        'host' : current_app.config['PUBLIC_ERDDAP']
    }
    url = 'http://%(host)s/erddap/metadata/iso19115/xml/' % args
    return url


def notify_incomplete_deployments(username):
    # Calculate the date two weeks ago
    two_weeks_ago = datetime.now() - timedelta(weeks=2)

    # Query for deployments that are not completed, last updated more than two weeks ago, and match the username
    query = (Deployment.query.filter(Deployment.completed == False,
                                     Deployment.updated < two_weeks_ago,
                                     Deployment.username == username)
                                     .order_by(Deployment.updated))

    # Convert the cursor to a list
    deployments = query.all()

    # Check if there are any deployments to notify about
    if not deployments:
        return

    # Prepare email content
    subject = f"Reminder: Incomplete Deployments for {username}"

    # Start building the HTML table
    body = f"""
    <html>
    <body>
        <p>User {username} has the following incomplete glider deployment(s) on the IOOS Glider DAC that were last updated more than two weeks ago.
           Please mark the following deployment(s) as complete if the associated deployments have finished.</p>
        <table border="1" style="border-collapse: collapse;">
            <tr>
                <th>Deployment Name</th>
                <th>Last Updated</th>
            </tr>
    """

    for deployment in deployments:
        body += f"""
            <tr>
                <td>{deployment.name}</td>
                <td>{deployment.updated.strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
        """

    body += """
        </table>
    </body>
    </html>
    """

    msg = Message(subject, recipients=[user["email"]])
    msg.html = body

    send_email_wrapper(msg)
