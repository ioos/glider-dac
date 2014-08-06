import os
from flask.ext.mail import Message

from flask import render_template
from glider_dac import app, mail

def send_wmoid_email(username, deployment):
    # sender comes from MAIL_DEFAULT_SENDER in env
    subject        = "New Glider Deployment - %s" % deployment.name
    recipients     = [app.config.get('MAIL_DEFAULT_TO')]
    cc_recipients  = []
    if app.config.get('MAIL_DEFAULT_LIST') is not None:
        cc_recipients.append(app.config.get('MAIL_DEFAULT_LIST'))

    msg            = Message(subject, recipients=recipients, cc=cc_recipients)
    msg.body       = render_template('wmoid_email.txt', deployment=deployment, username=username)

    mail.send(msg)

