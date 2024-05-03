import pytest
from pytest_bdd import scenarios, scenario, given, when, then

import os
import shutil
from flask_login import current_user
from glider_dac import create_app
from glider_dac.extensions import db
from glider_dac.models.user import User
from glider_dac.models.deployment import Deployment
from passlib.hash import sha512_crypt

# Load all scenarios from the feature file
# why is app context even needed here?
with create_app().app_context():
    scenarios("../features/deployment_operations.feature")

@pytest.fixture
def app():
    os.environ["FLASK_ENV"] = "TESTING"
    app = create_app()

    # Create all database tables
    with app.app_context():
        db.create_all()

        yield app


@pytest.fixture(autouse=True)
def clear_database(app):
    # Clean up before each scenario
    db.session.remove()
    # Drop all tables
    db.drop_all()
    # Create all tables
    db.create_all()
    # Yield to the test
    db.session.commit()
    # Clean up
    #with app.app_context():
    for path in os.listdir(app.config["DATA_ROOT"]):
        if path == '.gitignore':
            continue
        full_path = os.path.join(app.config["DATA_ROOT"], path)
        if os.path.isfile(full_path) or os.path.islink(full_path):
            os.unlink(full_path)
        else:
            shutil.rmtree(full_path)
    yield

@pytest.fixture
def client(app):
    with app.test_client() as t_client:
        return t_client

@pytest.fixture
def mail_recorder(app):
    yield app.mail.record_messages

@given("I am a logged in user")
def user_logged_in(client):
    user = User(username="testuser", name="Test User",
                password=sha512_crypt.hash("Datamanagement101"))
    db.session.add(user)
    db.session.commit()
    # Make a login request
    with client:
        response = client.post('/login', data={'username': 'testuser', 'password': 'Datamanagement101'},
                               follow_redirects=True)

        # Check response
        assert response.status_code == 200
        assert current_user == user and current_user.is_authenticated

# Needs to be in separate named fixture since pytest-bdd does name munging.
# First call creates the deployment, and # subsequent calls can re-refer to the
# fixture to fetch the email content it sends
@pytest.fixture
def create_deployment_and_capture_email(client, mail_recorder, app):
    with mail_recorder() as outbox:
        response = client.post('/users/testuser/deployment/new', data={'glider_name': 'testdeployment', 'deployment_date': '2024-05-02T0000',
                                                                    'attribution': 'Automated Glider Tests'},
                               follow_redirects=True)
    assert response.status_code == 200
    deployment = Deployment.query.filter_by(glider_name="testdeployment").one_or_none()
    assert deployment is not None
    # Return deployment object and email messages
    yield outbox

@when("I create a new glider deployment")
def step_create_glider_deployment(create_deployment_and_capture_email):
    # step creates the deployment and then sets previous fixture for the future yield
    pass

@then("the requisite folder hierarchy should be created in the submission folder")
def deployment_folder_hierarchy(app):
    deployment_dir_location = "tests/test_fs/data/submission/testuser/testdeployment-20240502T0000"
    assert (os.path.exists(deployment_dir_location) and os.path.isdir(deployment_dir_location) and
            os.path.isfile(os.path.join(deployment_dir_location, "deployment.json")))

@then("an email should be sent notifying Glider DAC administrators of the new deployment")
def deployment_email_notification(app, create_deployment_and_capture_email):
    outbox = create_deployment_and_capture_email
    message = outbox[0]
    assert message.sender == app.config["MAIL_DEFAULT_SENDER"]
    assert message.send_to == set(app.config["MAIL_DEFAULT_TO"].split(";"))
    assert message.subject == "New Glider Deployment - testdeployment-20240502T0000"
