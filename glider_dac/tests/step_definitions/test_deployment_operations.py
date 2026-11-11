import pytest
from pytest_bdd import scenarios, given, when, then, parsers

import filecmp
import os
import shutil
from pathlib import Path
from glob import glob
import json
from flask import url_for
from flask_login import current_user
import glider_dac
from datetime import datetime, timezone
from glider_dac.tests.resources import STATIC_FILES
from glider_dac.extensions import db
from glider_dac.models.deployment import Deployment
from netCDF4 import Dataset
from compliance_checker.suite import CheckSuite
from datetime import datetime, timedelta
from glider_dac.models.deployment import Deployment
from glider_dac.models.user import User

# Load all scenarios from the feature file
# why is app context even needed here?
with glider_dac.create_app().app_context():
    scenarios("../features/deployment_operations.feature")


@pytest.fixture(autouse=True)
def setup_test_env():
    os.environ["FLASK_ENV"] = "TEST_CONFIG"


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
    for top_level in (
        app.config["DATA_ROOT"],
        app.config["PRIV_DATA_ROOT"],
        app.config["PUBLIC_DATA_ROOT"],
        app.config["ARCHIVE_PATH"],
    ):
        for path in os.listdir(top_level):
            if path == ".gitignore":
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
def user_logged_in(client, app):
    # set up Flask-Security user related code
    ds = app.security.datastore
    with app.app_context():
        ds.db.create_all()

        r1 = ds.create_role(name="basic")
        user = ds.create_user(
            username="testuser",
            name="Test User",
            email="test@nonexistent.noemail",
            password="Datamanagement101",
            roles=[r1],
        )
        ds.commit()

        with client:
            response = client.post(
                "/login",
                data={"username": "testuser", "password": "Datamanagement101"},
                follow_redirects=True,
            )

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
            response = client.post(
                "/users/testuser/deployment/new",
                data={
                    "glider_name": "testdeployment",
                    "deployment_date": "2024-05-02T0000",
                    "attribution": "Automated Glider Tests",
                },
                follow_redirects=True,
            )
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
    deployment_dir_location = (
        f"{app.config['DATA_ROOT']}/testuser/testdeployment-20240502T0000"
    )
    assert (
        os.path.exists(deployment_dir_location)
        and os.path.isdir(deployment_dir_location)
        and os.path.isfile(os.path.join(deployment_dir_location, "deployment.json"))
    )


@then(
    "an email should be sent notifying Glider DAC administrators of the new deployment"
)
def deployment_email_notification(app, create_deployment_and_capture_email):
    outbox = create_deployment_and_capture_email
    message = outbox[0]
    assert message.sender == app.config["MAIL_DEFAULT_SENDER"]
    assert message.send_to == set(app.config["MAIL_DEFAULT_TO"].split(";"))
    assert message.subject == "New Glider Deployment - testdeployment-20240502T0000"


@given(
    "a corresponding real-time deployment belongs to another user",
    target_fixture="real_time_deployment",
)
def real_time_deployment_owned_by_another_user(app):
    user = app.security.datastore.create_user(
        username="realtimeowner",
        name="Real-time Owner",
        email="realtime@example.invalid",
        password="RealtimeTestPassword",
    )
    app.security.datastore.commit()
    deployment = Deployment(
        user=user,
        name="testdeployment-20240502T0000",
        glider_name="testdeployment",
        deployment_date=datetime(2024, 5, 2),
        updated=datetime.now(tz=timezone.utc),
        deployment_dir="realtimeowner/testdeployment-20240502T0000",
        operator="Real-time Operator",
        attribution="Real-time Attribution",
        wmo_id="1234567",
        completed=False,
        delayed_mode=False,
    )
    db.session.add(deployment)
    deployment.save()
    shutil.copy(STATIC_FILES["murphy"], Path(deployment.full_path) / "existing.nc")
    return deployment


@given("the real-time deployment is completed")
def real_time_deployment_completed(real_time_deployment):
    real_time_deployment.completed = True
    real_time_deployment.save()


@given("the real-time deployment is not completed")
def real_time_deployment_incomplete(real_time_deployment):
    assert not real_time_deployment.completed


@when(
    "I create a new delayed mode glider deployment",
    target_fixture="delayed_creation_result",
)
def create_delayed_mode_deployment(client, mail_recorder, real_time_deployment):
    source_path = Path(real_time_deployment.full_path)
    snapshot = {
        column.name: getattr(real_time_deployment, column.name)
        for column in Deployment.__table__.columns
    }
    source_metadata = (source_path / "deployment.json").read_bytes()
    with mail_recorder() as outbox:
        response = client.post(
            f"/users/testuser/deployment/{real_time_deployment.name}/new"
        )
    return response, outbox, snapshot, source_metadata


@then("the delayed mode deployment should be created successfully")
def delayed_mode_deployment_created(
    delayed_creation_result, real_time_deployment, app
):
    response, outbox, _, _ = delayed_creation_result
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/users/testuser/deployments")
    db.session.expire_all()
    delayed = Deployment.query.filter_by(
        name=f"{real_time_deployment.name}-delayed"
    ).one()
    assert delayed.delayed_mode
    assert not delayed.completed
    assert delayed.user.username == "testuser"
    assert delayed.user_id != real_time_deployment.user_id
    for attribute in (
        "glider_name", "deployment_date", "operator", "attribution", "wmo_id"
    ):
        assert getattr(delayed, attribute) == getattr(real_time_deployment, attribute)
    assert delayed.deployment_dir == f"testuser/{delayed.name}"
    metadata_path = Path(delayed.full_path) / "deployment.json"
    assert metadata_path.is_file()
    metadata = json.loads(metadata_path.read_text())
    assert metadata["name"] == delayed.name
    assert metadata["delayed_mode"]
    assert len(outbox) == 1
    assert outbox[0].subject == f"New Glider Deployment - {delayed.name}"
    assert outbox[0].send_to == set(app.config["MAIL_DEFAULT_TO"].split(";"))


@then("I should receive a completion-required error message")
def delayed_creation_requires_completed_source(delayed_creation_result, client):
    response, _, snapshot, _ = delayed_creation_result
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/users/testuser/deployments")
    page = client.get(response.headers["Location"])
    assert page.status_code == 200
    message = (
        f"The real time {snapshot['name']} must be marked as complete "
        "before adding delayed mode data"
    )
    assert message.encode() in page.data


@then("no delayed mode deployment should be created")
def delayed_mode_deployment_not_created(delayed_creation_result, app):
    _, outbox, snapshot, _ = delayed_creation_result
    db.session.expire_all()
    delayed_name = f"{snapshot['name']}-delayed"
    assert Deployment.query.filter_by(name=delayed_name).first() is None
    assert not outbox
    assert not list(Path(app.config["DATA_ROOT"]).glob(f"*/{delayed_name}"))


@then("the real-time deployment should remain unchanged")
def real_time_deployment_unchanged(delayed_creation_result):
    _, _, snapshot, source_metadata = delayed_creation_result
    db.session.expire_all()
    deployment = db.session.get(Deployment, snapshot["id"])
    assert deployment is not None
    assert {
        column.name: getattr(deployment, column.name)
        for column in Deployment.__table__.columns
    } == snapshot
    source_path = Path(deployment.full_path)
    assert (source_path / "deployment.json").read_bytes() == source_metadata
    assert filecmp.cmp(
        STATIC_FILES["murphy"], source_path / "existing.nc", shallow=False
    )


# deletion scenario
@when("I attempt to delete an existing deployment belonging to my user")
def delete_deployment_hierarchy(client):
    response = client.post(
        "/users/testuser/deployment/testdeployment-20240502T0000/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200


@then(
    "the requisite folder hierarchy and any folders should be removed from the submission, ERDDAP, and THREDDS locations"
)
def check_deployment_folders_deleted():
    search_pattern = os.path.join(
        "tests", "test_fs", "**", "testdeployment-20240502T0000"
    )
    assert len(glob(search_pattern, recursive=True)) == 0


@then("the deployment should be deleted and no longer visible on any deployment page")
def deployment_model_gone(client):
    assert (
        Deployment.query.filter_by(name="testdeployment-20240502T0000").one_or_none()
        is None
    )
    # TODO: Any page may be a little strong.  Consider only checking from API results
    response = client.get("/api/deployment")
    assert all(
        deployment["name"] != "testdeployment-20240502T000"
        for deployment in json.loads(response.data)["results"]
    )


@given(parsers.parse('I access the deployment as an "{actor}"'))
def deployment_permission_actor(actor, client, app):
    deployment = Deployment.query.filter_by(name="testdeployment-20240502T0000").one()
    deployment.completed = True
    db.session.commit()
    shutil.copy(STATIC_FILES["murphy"], Path(deployment.full_path) / "existing.nc")
    if actor == "owner":
        return

    user = app.security.datastore.create_user(
        username="otheruser",
        name="Other User",
        email="other@example.invalid",
        password="PermissionTestPassword",
        admin=actor in ("admin", "inactive admin"),
    )
    app.security.datastore.commit()
    client.get("/logout")
    response = client.post(
        "/login",
        data={"username": user.username, "password": "PermissionTestPassword"},
    )
    assert response.status_code == 302
    if actor == "inactive admin":
        user.active = False
        db.session.commit()


@then("the deployment controls should use the owner's username")
def deployment_controls_use_owner(client):
    response = client.get("/deployment/testdeployment-20240502T0000")
    assert response.status_code == 200
    assert (
        b'action="/users/testuser/deployment/testdeployment-20240502T0000/edit"'
        in response.data
    )
    assert (
        b'action="/users/testuser/deployment/testdeployment-20240502T0000/delete"'
        in response.data
    )


@when(
    parsers.parse(
        'I post to the deployment "{operation}" endpoint using the "{url_user}" username'
    ),
    target_fixture="deployment_request",
)
def post_deployment_operation(client, operation, url_user):
    username = "otheruser" if url_user == "caller" else "testuser"
    endpoint = "new" if operation == "new delayed" else operation
    url = f"/users/{username}/deployment/testdeployment-20240502T0000/{endpoint}"
    if operation == "new real-time":
        response = client.post(
            f"/users/{username}/deployment/new",
            data={
                "glider_name": "newdeployment",
                "deployment_date": "2024-05-03T0000",
                "attribution": "Automated Glider Tests",
            },
        )
    elif operation == "files":
        with open(STATIC_FILES["murphy"], "rb") as netcdf_file:
            response = client.post(
                url, data={"file-0": (netcdf_file, "uploaded.nc")}
            )
    elif operation == "delete_files":
        response = client.post(url, json={"files": ["existing.nc"]})
    else:
        response = client.post(url, data={"operator": "Changed operator"})
    return operation, response, username


@then("the deployment request should return 403 without changing the deployment")
def deployment_permission_denied(deployment_request):
    _, response, _ = deployment_request
    assert response.status_code == 403
    db.session.expire_all()
    deployment = Deployment.query.filter_by(name="testdeployment-20240502T0000").one()
    assert deployment.operator != "Changed operator"
    assert filecmp.cmp(
        STATIC_FILES["murphy"], Path(deployment.full_path) / "existing.nc", shallow=False
    )
    assert not (Path(deployment.full_path) / "uploaded.nc").exists()
    assert Deployment.query.filter_by(
        name="testdeployment-20240502T0000-delayed"
    ).first() is None
    assert Deployment.query.filter_by(name="newdeployment-20240503T0000").first() is None


@then("the deployment operation should succeed")
def deployment_permission_allowed(deployment_request):
    operation, response, username = deployment_request
    expected_status = 200 if operation in ("files", "delete_files") else 302
    assert response.status_code == expected_status
    db.session.expire_all()
    deployment = Deployment.query.filter_by(name="testdeployment-20240502T0000").first()
    if operation == "delete":
        assert deployment is None
    elif operation == "edit":
        assert deployment.operator == "Changed operator"
    elif operation == "files":
        assert filecmp.cmp(
            STATIC_FILES["murphy"],
            Path(deployment.full_path) / "uploaded.nc",
            shallow=False,
        )
    elif operation == "delete_files":
        assert not (Path(deployment.full_path) / "existing.nc").exists()
    elif operation == "new delayed":
        delayed = Deployment.query.filter_by(
            name="testdeployment-20240502T0000-delayed"
        ).one()
        assert delayed.user.username == username
        assert delayed.deployment_dir == f"{username}/{delayed.name}"
        assert Path(delayed.full_path).is_dir()
    elif operation == "new real-time":
        created = Deployment.query.filter_by(name="newdeployment-20240503T0000").one()
        assert created.user.username == username
        assert not created.delayed_mode
        assert created.deployment_dir == f"{username}/{created.name}"
        assert Path(created.full_path).is_dir()


@when(
    parsers.parse('I post to the missing deployment "{operation}" endpoint'),
    target_fixture="missing_deployment_response",
)
def post_missing_deployment(client, operation):
    endpoint = "new" if operation == "new delayed" else operation
    return client.post(f"/users/testuser/deployment/missing/{endpoint}")


@then("the deployment request should return 404")
def missing_deployment_not_found(missing_deployment_response):
    assert missing_deployment_response.status_code == 404


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
    folder_path = (
        f"{app.config['PRIV_DATA_ROOT']}/testuser/testdeployment-20240502T0000/"
    )
    os.makedirs(folder_path)
    ds_path = os.path.join(folder_path, "testdeployment-20240502T0000.nc")
    shutil.copy(os.path.join(os.getcwd(), "../..", STATIC_FILES["murphy"]), ds_path)
    with Dataset(ds_path, "r"):
        pass


@when("the deployment exists in ERDDAP")
def erddap_deployment(app):
    # TODO: find reasonable DAP approximation of ERDDAP
    ds_path = f"{app.config['PRIV_DATA_ROOT']}/testuser/testdeployment-20240502T0000/testdeployment-20240502T0000.nc"
    yield Dataset(ds_path, "r")


@when(
    "the IOOS Compliance Checker has run the CF compliance checks against the deployment aggregation in ERDDAP"
)
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
    folder_path = (
        f"{app.config['PUBLIC_DATA_ROOT']}/testuser/testdeployment-20240502T0000/"
    )
    os.makedirs(folder_path)
    shutil.copy(
        os.path.join(os.getcwd(), "../..", STATIC_FILES["murphy"]),
        os.path.join(folder_path, "testdeployment-20240502T0000.ncCF.nc3.nc"),
    )


@then(
    "the NCEI archival script will link the aggregated deployment file to the archival directory"
)
def ncei_archival_script(app):
    # FIXME: import must go here due to config loading on module load, which is dependent on
    #        FLASK_ENV environment variable value
    from scripts import archive_datasets

    archive_datasets.main()
    file_path = f"{app.config['ARCHIVE_PATH']}/testdeployment-20240502T0000.ncCF.nc3.nc"
    # TODO: test that file exists and is working symlink
    assert os.path.islink(file_path)
    assert os.path.exists(file_path)  # link actual has valid contents
    assert os.path.exists(file_path + ".md5")


@given("a user exists")
def user_exists(app):
    user = User(
        username="notifyuser",
        name="Notify User",
        email="notify@example.com",
        password="pw",
    )
    app.extensions["sqlalchemy"].db.session.add(user)
    app.extensions["sqlalchemy"].db.session.commit()


@given("the user has a deployment that is incomplete and older than two weeks")
def user_has_old_incomplete_deployment(app):
    # TODO: Could user be stored in fixture rather than queried?
    user = User.query.filter_by(username="notifyuser").first()
    dep = Deployment(
        name="old_dep",
        user_id=user.id,
        completed=False,
        updated=datetime.utcnow() - timedelta(weeks=3),
    )
    app.extensions["sqlalchemy"].db.session.add(dep)
    app.extensions["sqlalchemy"].db.session.commit()


@when("the incomplete deployment notification is triggered")
def trigger_incomplete_notification(app, mocker):
    user = User.query.filter_by(username="notifyuser").first()
    mock_send = mocker.patch("glider_dac.models.user.send_email_wrapper")
    with app.app_context():
        user.notify_user_incomplete_deployments()
    # Store mock for assertion in next step
    trigger_incomplete_notification.mock_send = mock_send


@then("the user should receive an email listing the incomplete deployment")
def assert_incomplete_email_sent():
    mock_send = trigger_incomplete_notification.mock_send
    assert mock_send.called
    msg = mock_send.call_args[0][0]
    assert "old_dep" in msg.html


@given("there are deployments with different names, WMO IDs, and usernames")
def create_varied_deployments(app):
    with app.app_context():
        user1 = User(
            username="kraken_user",
            name="Kraken",
            email="kraken@nonexistent.noemail",
            password="pw",
            active=True,
            fs_uniquifier="xx1",
        )
        user2 = User(
            username="miskatonic",
            name="Miskatonic",
            email="miskatonic@nonexistent.noemail",
            password="pw",
            active=True,
            fs_uniquifier="xx2",
        )
        db.session.add_all([user1, user2])
        db.session.commit()
        dep1 = Deployment(
            name="kraken_alpha",
            wmo_id="12345",
            user_id=user1.id,
            glider_name="kraken",
            deployment_dir="nonexistent1",
            updated=datetime.now(tz=timezone.utc),
        )
        dep2 = Deployment(
            name="gliderx",
            wmo_id="67890",
            user_id=user2.id,
            glider_name="gliderx",
            deployment_dir="nonexistent2",
            updated=datetime.now(tz=timezone.utc),
        )
        db.session.add_all([dep1, dep2])
        db.session.commit()


@when('I filter deployments by name "kraken"', target_fixture="name_response")
def filter_by_name(client):
    return client.get(url_for("index.index", name="kraken"))


@then('only deployments with "kraken" in the name should be shown')
def check_name_filter(name_response):
    data = name_response.data.decode()
    assert "kraken_alpha" in data
    assert "gliderx" not in data


@when('I filter deployments by WMO ID "12345"', target_fixture="wmo_response")
def filter_by_wmo_id(client):
    return client.get(url_for("index.index", wmo_id="12345"))


@then('only deployments with WMO ID "12345" should be shown')
def check_wmo_id_filter(wmo_response):
    data = wmo_response.data.decode()
    assert "kraken_alpha" in data
    assert "gliderx" not in data


@when(
    'I filter deployments by username "miskatonic"', target_fixture="username_response"
)
def filter_by_username(client):
    return client.get(url_for("index.index", username="miskatonic"))


@then('only deployments with username "miskatonic" should be shown')
def check_username_filter(username_response):
    data = username_response.data.decode()
    assert "gliderx" in data
    assert "kraken_alpha" not in data


# New steps for updating user profile without changing password


@when("I update my user profile leaving password blank")
def update_profile_leave_password_blank(client):
    response = client.post(
        "/users/testuser",
        data={
            "username": "testuser",
            "name": "Updated Name",
            "email": "updated@example.com",
            "organization": "",
            "password": "",
            "confirm": "",
            "submit": "Submit",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


@when("I log out")
def do_log_out(client):
    response = client.get("/logout", follow_redirects=True)
    # allow either 200 or 302 depending on app routes
    assert response.status_code in (200, 302)


@then("I should still be able to log in with original password")
def can_relogin_with_original_password(client, app):
    # ensure logged out then login
    with client:
        resp = client.post(
            "/login",
            data={"username": "testuser", "password": "Datamanagement101"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert current_user.is_authenticated
        assert current_user.username == "testuser"


@then("my updated name and email should be saved")
def check_name_email_saved(app):
    user = User.query.filter_by(username="testuser").one()
    assert user.name == "Updated Name"
    assert user.email == "updated@example.com"
