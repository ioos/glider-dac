from glider_dac import glider_emails, mail, app
#from unittest import TestCase
import pytest
import smtplib
from bson.objectid import ObjectId
import datetime
from unittest.mock import patch
from types import SimpleNamespace

@pytest.fixture
def deployment():
    data_dict = {
        '_id': ObjectId('000000000000000000000000'),
        'username': 'someone',
        'updated': datetime.datetime(2022, 2, 16, 21, 32, 49, 793000),
        'estimated_deploy_location': '',
        'user_id': ObjectId('111111111111111111111111'),
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

@patch("glider_dac.mail")
def test_email_exception(client, deployment, caplog, monkeypatch):
    username = deployment.username
    app.config["MAIL_ENABLED"] = True
    def smtp_error_raiser(message):
        raise smtplib.SMTPException("Mock email failure")
    monkeypatch.setattr(mail, "send", smtp_error_raiser)
    with app.app_context():
        glider_emails.send_registration_email(username, deployment)
    assert caplog.records[-1].msg.startswith("Exception occurred while attempting "
                                             "to send email: ")
