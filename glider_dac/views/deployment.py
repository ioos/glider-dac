#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
glider_dac/views/deployment.py
View definition for Deployments
"""

from cf_units import Unit
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse as dateparse
from flask import (
    Blueprint,
    Response,
    current_app,
    render_template,
    redirect,
    stream_with_context,
    jsonify,
    flash,
    url_for,
    request
)
from flask_cors import cross_origin
from flask_wtf import FlaskForm
from flask_login import login_required, current_user
from glider_dac.extensions import db
from glider_dac.models.deployment import Deployment, DeploymentSchema
from glider_dac.models.user import User
from glider_dac.services.emails import send_registration_email
from multidict import CIMultiDict
from pathlib import Path
from wtforms import StringField, SubmitField, BooleanField, validators
import re
import json
import os

deployment_bp = Blueprint("deployment", __name__)


def is_date_parseable(form, field):
    try:
        dateparse(field.data)
    except ValueError:
        raise validators.ValidationError("Invalid Date")


def is_valid_glider_name(form, field):
    regex = r"^[a-zA-Z]+[a-zA-Z0-9-_]*$"
    if not re.match(regex, field.data):
        raise validators.ValidationError("Invalid Glider Name")


def deployment_key_fn(dep):
    """
    Helper function for sorting deployments.  Returns the "updated" attribute
    timestamp (defaulting to 1970-01-01 if not found), followed by the
    deployment name as the sorting key.
    """
    default_dt = datetime(1970, 1, 1)
    return getattr(dep, "updated", default_dt), dep.name


class DeploymentForm(FlaskForm):
    operator = StringField("Operator")
    completed = BooleanField("Completed")
    archive_safe = BooleanField("Submit to NCEI on Completion")
    attribution = StringField("Attribution")
    submit = SubmitField("Submit")


class NewDeploymentForm(FlaskForm):
    glider_name = StringField("Glider Name", [is_valid_glider_name])
    deployment_date = StringField("Deployment Date", [is_date_parseable])
    attribution = StringField("Attribution")
    delayed_mode = BooleanField("Delayed Mode?")
    submit = SubmitField("Create")


@deployment_bp.route("/users/<string:username>/deployments")
def list_user_deployments(username):
    # TODO: add error case
    user = User.query.filter_by(username=username).one_or_none()
    deployments = Deployment.query.filter_by(user=user).all()

    kwargs = {}
    if (
        current_user
        and current_user.is_active
        and (current_user.admin or current_user == user)
    ):
        # Permission to edit
        form = NewDeploymentForm()
        kwargs["form"] = form

    for m in deployments:
        if not os.path.exists(m.full_path):
            continue

        m.updated = datetime.utcfromtimestamp(os.path.getmtime(m.full_path))

    deployments.sort(key=deployment_key_fn)

    return render_template(
        "user_deployments.html", username=username, deployments=deployments, **kwargs
    )


@deployment_bp.route("/operators/<path:operator>/deployments")
def list_operator_deployments(operator):
    deployments = (
        Deployment.query.filter(Deployment.operator == operator)
        .order_by(Deployment.updated, Deployment.name)
        .all()
    )

    for m in deployments:
        if not os.path.exists(m.full_path):
            continue

        m.updated = datetime.utcfromtimestamp(os.path.getmtime(m.full_path))

    return render_template(
        "operator_deployments.html", operator=operator, deployments=deployments
    )


@deployment_bp.route("/deployment/<path:deployment_name>")
def show_deployment(deployment_name):
    deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()
    # TODO: consider refactoring model property to return Path instead
    dep_path = Path(deployment.full_path)

    files = []
    for f in dep_path.glob("*.nc"):
        file_mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        file_loc = (
            Path(current_app.config["PRIV_DATA_ROOT"])
            / Path(deployment.full_path).relative_to(current_app.config["DATA_ROOT"])
            / f.name
        )
        file_exists = file_loc.exists()
        if file_exists:
            try:
                file_status = os.getxattr(file_loc, "user.file_status")
            except OSError:
                file_status = None
            try:
                qc_status = os.getxattr(file_loc, "user.qc_run") not in (None, "error")
            except OSError:
                qc_status = False

        files.append(
            (
                f.name,
                file_mtime,
                file_exists,
                file_status,
                qc_status,
            )
        )

    # sort by mtime
    files.sort(key=lambda a: a[1])

    kwargs = {}

    extra_atts_path = dep_path / "extra_atts.json"

    try:
        (extra_atts_path.read_text("utf-8") if extra_atts_path.exists() else None)
    except OSError:
        current_app.logger.exception(f"Could not read {extra_atts_path}")

    form = DeploymentForm(obj=deployment)

    if current_user.is_authenticated and (
        current_user.is_active
        and (current_user.admin or current_user == deployment.user)
    ):
        kwargs["editable"] = True
        if current_user.is_authenticated and (
            current_user.admin or current_user.username == deployment.user.username
        ):
            kwargs["admin"] = True

    current_app.logger.info(deployment.dap)
    return render_template(
        "show_deployment.html",
        form=form,
        deployment=deployment,
        username=getattr(current_user, "username", None),
        files=files,
        **kwargs,
    )


@deployment_bp.route("/deployment/<path:deployment_name>/events")
def deployment_events(deployment_name):
    def event_stream():
        last_id = "0"
        def dt_fn():
            return datetime.now(tz=timezone.utc).isoformat()
        stream_key = f"deployment:{deployment_name}"
        yield f"[{dt_fn()}] Listerning for filesystem events on {deployment_name}:\n"
        while True:
            events = current_app.redis_connection.xread(
                {stream_key: last_id}, block=1000, count=50
            )
            for key, event_list in events:
                for event_id, event_data in event_list:
                    last_id = event_id
                    # Convert bytes to strings
                    event_data = {k.decode(): v.decode() for k, v in event_data.items()}
                    yield f"[{dt_fn()}] data: {json.dumps(event_data)}\n\n"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


@deployment_bp.route("/users/<string:username>/deployment/new", methods=["POST"])
@login_required
def new_deployment(username):
    user = User.query.filter_by(username=username).one_or_none()
    if user is None or (
        user is not None and not current_user.admin and current_user != user
    ):
        # No permission
        flash("Permission denied", "danger")
        return redirect(url_for("index.index"))

    form = NewDeploymentForm()

    if form.validate_on_submit():
        deployment_date = dateparse(form.deployment_date.data)
        delayed_mode = form.delayed_mode.data
        deployment_name = (
            form.glider_name.data + "-" + deployment_date.strftime("%Y%m%dT%H%M")
        )
        if delayed_mode:
            deployment_name += "-delayed"

        try:
            # TODO: should this be handled at SQLAlchemy level?
            existing_deployment = Deployment.query.filter_by(
                name=deployment_name
            ).one_or_none()
            if existing_deployment is not None:
                # TODO: Raise more appropriate exception?
                raise ValueError("Duplicate Key Detected: name")
            # TODO: Consolidate logic
            existing_deployment = Deployment.query.filter_by(
                glider_name=form.glider_name.data, deployment_date=deployment_date
            ).one_or_none()
            if existing_deployment is not None:
                # if there is a previous real-time deployment and the one
                # to create is marked as delayed mode, act as if the delayed
                # mode modification path had been followed
                if not existing_deployment.delayed_mode and delayed_mode:
                    return new_delayed_mode_deployment(
                        username, existing_deployment._id
                    )
            # same combination of glider_name/date/delayed_or_rt_mode should
            # have been caught by this point by the unique deployment name.
            # If we reach this, point, the deployment should either not exist
            # yet, or delayed_mode on the existing deployment should be true and the
            # new one should be a real-time deployment, so just continue making
            # the deployment normally.
            deployment = Deployment()
            deployment.user = user
            deployment.user.username = username
            deployment.deployment_dir = os.path.join(username, deployment_name)
            deployment.updated = datetime.utcnow()
            deployment.deployment_date = deployment_date
            deployment.glider_name = form.glider_name.data
            deployment.name = deployment_name
            deployment.attribution = form.attribution.data
            deployment.delayed_mode = delayed_mode
            db.session.add(deployment)
            db.session.commit()
            deployment.sync()
            flash("Deployment created", "success")
            send_registration_email(deployment.user.username, deployment)
        # TODO: handle prior to creation
        # except DuplicateKeyError:
        except Exception as e:
            raise (e)
            flash(
                "Deployment names must be unique across Glider DAC: %s already used"
                % deployment_name,
                "danger",
            )

    else:
        error_str = ", ".join(
            ["%s: %s" % (k, ", ".join(v)) for k, v in form.errors.items()]
        )
        flash("Deployment could not be created: %s" % error_str, "danger")

    return redirect(url_for("deployment.list_user_deployments", username=username))


@deployment_bp.route(
    "/users/<string:username>/deployment/<string:deployment_name>/new", methods=["POST"]
)
@login_required
def new_delayed_mode_deployment(username, deployment_name):
    """
    Endpoint for submitting a delayed mode deployment from an existing
    realtime deployment

    :param string username: Username
    :param str deployment_name: Name of the existing realtime deployment
    """
    user = User.query.filter_by(username=username).one_or_none()
    if user is None or (
        user is not None and not current_user.admin and current_user != user
    ):
        # No permission
        flash("Permission denied", "danger")
        return redirect(url_for("index.index"))

    rt_deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()
    # Need to check if the "real time" deployment is complete yet
    if not rt_deployment.completed:
        url_for(
            "deployment.show_deployment",
            username=username,
            deployment_name=deployment_name,
        )
        flash(
            "The real time %s must be marked as complete before adding delayed mode data"
            % rt_deployment.name,
            "danger",
        )
        return redirect(url_for("deployment.list_user_deployments", username=username))

    deployment = Deployment()
    deployment.name = rt_deployment.name + "-delayed"
    # deployment.user_id = user.user_id
    deployment.user.username = username
    deployment.operator = rt_deployment.operator
    deployment.deployment_dir = os.path.join(username, deployment_name)
    deployment.wmo_id = rt_deployment.wmo_id
    deployment.updated = datetime.utcnow()
    deployment.glider_name = rt_deployment.glider_name
    deployment.deployment_date = rt_deployment.deployment_date
    deployment.attribution = rt_deployment.attribution
    deployment.delayed_mode = True
    db.session.add(deployment)
    db.session.commit()
    flash("Deployment created", "success")
    send_registration_email(deployment.user.username, deployment)

    return redirect(url_for("deployment.list_user_deployments", username=username))


@deployment_bp.route(
    "/users/<string:username>/deployment/<string:deployment_name>/edit",
    methods=["POST"],
)
@login_required
def edit_deployment(username, deployment_name):
    user = User.query.filter_by(username=username).one_or_none()
    if user is None or (
        user is not None and not current_user.admin and current_user != user
    ):
        # No permission
        flash("Permission denied", "danger")
        return redirect(url_for("deployment.list_user_deployments", username=username))

    deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()

    form = DeploymentForm(obj=deployment)

    if form.validate_on_submit():
        form.populate_obj(deployment)
        deployment.updated = datetime.utcnow()
        db.session.commit()
        flash("Deployment updated", "success")
        return redirect(
            url_for(
                "deployment.show_deployment",
                username=username,
                deployment_name=deployment.name,
            )
        )
    else:
        error_str = ", ".join(
            ["%s: %s" % (k, ", ".join(v)) for k, v in form.errors.items()]
        )
        flash("Deployment could not be edited: %s" % error_str, "danger")

    return render_template(
        "edit_deployment.html", username=username, form=form, deployment=deployment
    )


@deployment_bp.route(
    "/users/<string:username>/deployment/<string:deployment_name>/files",
    methods=["POST"],
)
@login_required
def post_deployment_file(username, deployment_name):
    deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()
    user = User.query.filter_by(username=username).one_or_none()

    if not (
        deployment
        and user
        and deployment.user.username == user.username
        and (current_user.admin or current_user == user)
    ):
        raise Exception("Unauthorized")  # @TODO better response via ajax?

    retval = []
    for name, f in request.files.items():
        if not name.startswith("file-"):
            continue

        safe_filename = f.filename  # @TODO

        out_name = os.path.join(deployment.full_path, safe_filename)

        try:
            with open(out_name, "wb") as of:
                f.save(of)
        except Exception:
            current_app.logger.exception("Error uploading file: {}".format(out_name))

        retval.append((safe_filename, datetime.utcnow()))
    editable = (
        current_user
        and current_user.is_active
        and (current_user.admin or current_user == user)
    )

    return render_template("_deployment_files.html", files=retval, editable=editable)


@deployment_bp.route(
    "/users/<string:username>/deployment/<string:deployment_name>/delete_files",
    methods=["POST"],
)
@login_required
def delete_deployment_files(username, deployment_name):
    deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()
    user = User.query.filter_by(username=username).one_or_none()
    if deployment is None:
        # @TODO better response via ajax?
        raise Exception("Unauthorized")
    if user is None:
        # @TODO better response via ajax?
        raise Exception("Unauthorized")
    if not (
        current_user
        and current_user.is_active
        and (current_user.admin or current_user == user)
    ):
        # @TODO better response via ajax?
        raise Exception("Unauthorized")

    if not (
        deployment and user and (current_user.admin or user._id == deployment.user_id)
    ):
        # @TODO better response via ajax?
        raise Exception("Unauthorized")

    for name in request.json["files"]:
        file_name = os.path.join(deployment.full_path, name)
        os.unlink(file_name)

    return ""


@deployment_bp.route(
    "/users/<string:username>/deployment/<string:deployment_name>/delete",
    methods=["POST"],
)
@login_required
def delete_deployment(username, deployment_name):
    deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()
    user = User.query.filter_by(username=username).one_or_none()
    if deployment is None:
        flash("Permission denied", "danger")
        return redirect(
            url_for(
                "deployment.show_deployment",
                username=username,
                deployment_name=deployment_name,
            )
        )
    if user is None:
        flash("Permission denied", "danger")
        return redirect(
            url_for(
                "deployment.show_deployment",
                username=username,
                deployment_name=deployment_name,
            )
        )
    if not (
        current_user
        and current_user.is_active
        and (current_user.admin or current_user == user)
    ):
        flash("Permission denied", "danger")
        return redirect(
            url_for(
                "deployment.show_deployment",
                username=username,
                deployment_name=deployment_name,
            )
        )

    # TODO: consider moving back to task queue?
    deployment.delete_deployment()
    flash("Deployment and associated files deleted", "success")

    return redirect(url_for("deployment.list_user_deployments", username=username))


# TODO: Is this method even needed anymore?
@deployment_bp.route("/api/deployment", methods=["GET"])
@cross_origin()
def get_deployments():
    """
    API endpoint to fetch deployment info
        ---
    parameters:
      - in: query
        name: completed
        required: false
        schema:
          type: boolean
        description: >
          Filter datasets by the completed attribute
      - in: query
        name: delayed_mode
        required: false
        schema:
          type: boolean
        description: >
          Filter datasets by the delayed_mode attribute
      - in: query
        name: minTime
        required: false
        schema:
          type: string
        example: now-12hr
        description: >
          Filter datasets with by last file's modtime being newer than minTime.
          Enter a datetime string (yyyy-MM-ddTHH:mm:ssZ)
          Or specify 'now-nUnits' for example now-12hr (integers only!)
    responses:
        200:
          description: Success
        400:
          description: Bad Request
        500:
          description: Internal Server Error
        501:
          description: Not Implemented
    """
    query = Deployment.query

    completed = request.args.get("completed")
    if completed in {"true", "false"}:
        query = query.filter(Deployment.completed == (completed == "true"))

    delayed_mode = request.args.get("delayed_mode")
    if delayed_mode in {"true", "false"}:
        query = query.filter(Deployment.delayed_mode == (delayed_mode == "true"))

    min_time = request.args.get("minTime")
    if min_time:

        def parse_date(datestr):
            try:
                if datestr.startswith("now-"):
                    match = re.match(r"^now-(\d+)\s*(\w+)$", datestr)
                    if match:
                        val, units = int(match.group(1)), match.group(2)
                        dt_now = datetime.now(tz=timezone.utc)
                        return dt_now - timedelta(**{units: val})
                return dateparse(datestr)
            except Exception:
                return None

        min_time_dt = parse_date(min_time)
        if min_time_dt:
            query = query.filter(Deployment.latest_file_mtime >= min_time_dt)

    deployments = query.all()
    from glider_dac.models.deployment import DeploymentSchema

    schema = DeploymentSchema(many=True)
    results = schema.dump(deployments)
    for d in results:
        d.pop("user_id", None)
        d.pop("compliance_check_report", None)
    return jsonify(results=results, num_results=len(results))
