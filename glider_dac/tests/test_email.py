from glider_dac import create_app
from flask import current_app
import glider_dac.services.emails as glider_email
#from unittest import TestCase
import pytest
import smtplib
import datetime
from unittest.mock import patch
from types import SimpleNamespace

@pytest.fixture
def deployment():
    data_dict = {
        'username': 'someone',
        'updated': datetime.datetime(2022, 2, 16, 21, 32, 49, 793000),
        'estimated_deploy_location': '',
        'name': 'SG610-20140715T1400',
        'archive_safe': True,
        'created': datetime.datetime(2017, 12, 4, 14, 33, 48, 513000),
        'checksum': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        'completed': True,
        'deployment_dir': 'fake/fake_deploy-20141214T1400',
        'deployment_date': datetime.datetime(2014, 12, 14, 14, 0),
        'glider_name': 'fake_deploy',
        'wmo_id': '00000',
        'operator': 'Some organization',
        'attribution': 'This data is not real',
        'estimated_deploy_date': None,
        'delayed_mode': False,
        'latest_file': 'fake_deploy.nc',
        'latest_file_mtime': datetime.datetime(2017, 9, 14, 14, 36, 19, 510000)
    }
    return SimpleNamespace(**data_dict)

@pytest.fixture
def client():
   app.config["MAIL_ENABLED"] = True
   app.config["TESTING"] = True
   app.config["MAIL_SERVER"] = "localhost"
   app.config["SERVER_NAME"] = "localhost"
   with app.test_client() as client:
       yield client

@patch("glider_dac.services.emails")
def test_email_exception(client, deployment, caplog, monkeypatch):
    app = create_app()
    username = deployment.username
    with app.app_context():
        current_app.config["MAIL_ENABLED"] = True
    def smtp_error_raiser(message):
        raise smtplib.SMTPException("Exception occurred while attempting to send email:")
    with current_app.app_context():
        monkeypatch.setattr(mail, "send", smtp_error_raiser)
        glider_email.send_registration_email(username, deployment)
    assert caplog.records[-1].msg.startswith("Exception occurred while attempting "
                                             "to send email: ")
