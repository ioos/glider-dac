import pytest
from pytest_bdd import scenarios, scenario, given, when, then

import os
import shutil
from glob import glob
import json
from flask_login import current_user
import glider_dac
from glider_dac.tests.resources import STATIC_FILES
from glider_dac.extensions import db
from glider_dac.models.user import User
from glider_dac.models.deployment import Deployment
from passlib.hash import sha512_crypt
from netCDF4 import Dataset
from compliance_checker.suite import CheckSuite

# Load all scenarios from the feature file
# why is app context even needed here?
with glider_dac.create_app().app_context():
    scenarios("../features/deployment_operations.feature")

@pytest.fixture(autouse=True)
def setup_test_env():
    os.environ["FLASK_ENV"] = "TESTING"

@pytest.fixture
def app(setup_test_env):
    app = glider_dac.create_app()

    # Create all database tables
    with app.app_context():
        db.create_all()

        yield app

@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    monkeypatch.chdir(os.path.dirname(glider_dac.__file__))

@pytest.fixture(autouse=True)
def clear_database(app, change_test_dir):
    # Clean up before each scenario
    db.session.remove()
    # Drop all tables
    db.drop_all()
    # Create all tables
    db.create_all()
    # Yield to the test
    db.session.commit()
    # Clean up
    for top_level in (app.config["DATA_ROOT"],
                      app.config["PRIV_DATA_ROOT"],
                      app.config["PUBLIC_DATA_ROOT"],
                      app.config["ARCHIVE_PATH"]):

        for path in os.listdir(top_level):
            if path == '.gitignore':
                continue
            full_path = os.path.join(top_level, path)
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
@pytest.fixture(scope="function")
def create_deployment_and_capture_email(client, mail_recorder, app):
    with mail_recorder() as outbox:
        with app.app_context():
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
    deployment_dir_location = f"{app.config['DATA_ROOT']}/testuser/testdeployment-20240502T0000"
    assert (os.path.exists(deployment_dir_location) and os.path.isdir(deployment_dir_location) and
            os.path.isfile(os.path.join(deployment_dir_location, "deployment.json")))

@then("an email should be sent notifying Glider DAC administrators of the new deployment")
def deployment_email_notification(app, create_deployment_and_capture_email):
    outbox = create_deployment_and_capture_email
    message = outbox[0]
    assert message.sender == app.config["MAIL_DEFAULT_SENDER"]
    assert message.send_to == set(app.config["MAIL_DEFAULT_TO"].split(";"))
    assert message.subject == "New Glider Deployment - testdeployment-20240502T0000"

# deletion scenario
@when("I attempt to delete an existing deployment belonging to my user")
def delete_deployment_hierarchy(client):
    response = client.post("/users/testuser/deployment/testdeployment-20240502T0000/delete", follow_redirects=True)
    assert response.status_code == 200

@then("the requisite folder hierarchy and any folders should be removed from the submission, ERDDAP, and THREDDS locations")
def check_deployment_folders_deleted():
    search_pattern = os.path.join("tests", "test_fs", '**', 'testdeployment-20240502T0000')
    assert len(glob(search_pattern, recursive=True)) == 0

@then("the deployment should be deleted and no longer visible on any deployment page")
def deployment_model_gone(client):
    assert Deployment.query.filter_by(name="testdeployment-20240502T0000").one_or_none() is None
    # TODO: Any page may be a little strong.  Consider only checking from API results
    response = client.get("/api/deployment")
    assert all(deployment["name"] != "testdeployment-20240502T000" for deployment in json.loads(response.data))

@when("the deployment has been marked as completed and ready for NCEI archival")
def deployment_created_and_ready_for_archival(create_deployment_and_capture_email):
    deployment = Deployment.query.filter_by(name="testdeployment-20240502T0000").one()
    deployment.completed = True
    deployment.ncei_archive = True
    db.session.commit()
    yield deployment

@when("the deployment directory has one or more valid glider NetCDF files")
def deployment_has_netcdf_files(app):
    # just copy our already existing private ERDDAP deployment
    folder_path = f"{app.config['PRIV_DATA_ROOT']}/testuser/testdeployment-20240502T0000/"
    os.makedirs(folder_path)
    ds_path = os.path.join(folder_path, "testdeployment-20240502T0000.nc")
    shutil.copy(os.path.join(os.getcwd(), "../..", STATIC_FILES['murphy']), ds_path)
    with Dataset(ds_path, "r"):
        pass


@when("the deployment exists in ERDDAP")
def erddap_deployment(app):
    # TODO: find reasonable DAP approximation of ERDDAP
    ds_path = f"{app.config['PRIV_DATA_ROOT']}/testuser/testdeployment-20240502T0000/testdeployment-20240502T0000.nc"
    yield Dataset(ds_path, "r")

@when("the IOOS Compliance Checker has run the CF compliance checks against the deployment aggregation in ERDDAP")
def compliance_checker_run(app, mocker):
    ds_path = f"{app.config['PRIV_DATA_ROOT']}/testuser/testdeployment-20240502T0000/testdeployment-20240502T0000.nc"
    ds = Dataset(ds_path, "r")

    # TODO: normally this would be called through glider_deployment_check
    # checkers don't load properly without this prelude
    cs = CheckSuite()
    cs.load_all_available_checkers()
    # imported as `from netCDF4 import Dataset` later on
    mocker.patch.object(CheckSuite, "load_dataset", new=lambda obj, loc: ds)
    deployment = Deployment.query.filter_by(name="testdeployment-20240502T0000").one()
    deployment.process_deployment()
    assert deployment.compliance_check_report is not None


@when("the single aggregated file exists in a folder with the NetCDF data")
def aggregated_file_exists(app):
    folder_path = f"{app.config['PUBLIC_DATA_ROOT']}/testuser/testdeployment-20240502T0000/"
    os.makedirs(folder_path)
    shutil.copy(os.path.join(os.getcwd(), "../..", STATIC_FILES['murphy']), os.path.join(folder_path, "testdeployment-20240502T0000.ncCF.nc3.nc"))


@then("the NCEI archival script will link the aggregated deployment file to the archival directory")
def ncei_archival_script(app):
    # FIXME: import must go here due to config loading on module load, which is dependent on
    #        FLASK_ENV environment variable value
    from scripts import archive_datasets
    archive_datasets.main()
    file_path = f"{app.config['ARCHIVE_PATH']}/testdeployment-20240502T0000.ncCF.nc3.nc"
    # TODO: test that file exists and is hard link
    assert (os.path.exists(file_path) and os.stat(file_path).st_nlink > 1 and
            os.path.exists(file_path + ".md5"))
