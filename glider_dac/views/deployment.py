#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
glider_dac/views/deployment.py
View definition for Deployments
'''
from cf_units import Unit
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse as dateparse
from flask import (current_app, render_template, redirect, jsonify, flash,
                   url_for, request)
from flask_cors import cross_origin
from flask_wtf import FlaskForm
from flask_login import login_required, current_user
from glider_dac.extensions import db
from glider_dac.models.deployment import Deployment, DeploymentSchema
from glider_dac.models.user import User
from glider_dac.models.deployment import Deployment
from glider_dac.services.emails import send_registration_email
from multidict import CIMultiDict
from wtforms import StringField, SubmitField, BooleanField, validators
from flask import Blueprint
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
    regex = r'^[a-zA-Z]+[a-zA-Z0-9-_]*$'
    if not re.match(regex, field.data):
        raise validators.ValidationError("Invalid Glider Name")

def deployment_key_fn(dep):
    """
    Helper function for sorting deployments.  Returns the "updated" attribute
    timestamp (defaulting to 1970-01-01 if not found), followed by the
    deployment name as the sorting key.
    """
    default_dt = datetime(1970, 1, 1)
    return getattr(dep, 'updated', default_dt), dep.name

class DeploymentForm(FlaskForm):
    operator = StringField('Operator')
    completed = BooleanField('Completed')
    archive_safe = BooleanField("Submit to NCEI on Completion")
    attribution = StringField('Attribution')
    submit = SubmitField('Submit')


class NewDeploymentForm(FlaskForm):
    glider_name = StringField('Glider Name', [is_valid_glider_name])
    deployment_date = StringField('Deployment Date', [is_date_parseable])
    attribution = StringField('Attribution')
    delayed_mode = BooleanField('Delayed Mode?')
    submit = SubmitField("Create")

@deployment_bp.route('/users/<string:username>/deployments')
def list_user_deployments(username):
    # TODO: add error case
    user = User.query.filter_by(username=username).one_or_none()
    deployments = Deployment.query.filter_by(user=user).all()

    kwargs = {}
    if current_user and current_user.is_active and (current_user.admin or
                                                    current_user == user):
        # Permission to edit
        form = NewDeploymentForm()
        kwargs['form'] = form

    for m in deployments:
        if not os.path.exists(m.full_path):
            continue

        m.updated = datetime.utcfromtimestamp(os.path.getmtime(m.full_path))

    deployments.sort(key=deployment_key_fn)

    return render_template('user_deployments.html', username=username,
                           deployments=deployments, **kwargs)


@deployment_bp.route('/operators/<path:operator>/deployments')
def list_operator_deployments(operator):
    deployments = (Deployment.query.filter(Deployment.operator == operator)
                             .order_by(Deployment.updated, Deployment.name)
                             .all())

    for m in deployments:
        if not os.path.exists(m.full_path):
            continue

        m.updated = datetime.utcfromtimestamp(os.path.getmtime(m.full_path))

    return render_template('operator_deployments.html', operator=operator,
                           deployments=deployments)


@deployment_bp.route('/deployment/<path:deployment_name>')
def show_deployment(deployment_name):
    deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()

    files = []
    for dirpath, dirnames, filenames in os.walk(deployment.full_path):
        for f in filenames:
            if f.endswith('.nc'):
                files.append((f, datetime.utcfromtimestamp(
                    os.path.getmtime(os.path.join(dirpath, f)))))

    files.sort(key=lambda a: a[1])

    kwargs = {}

    form = DeploymentForm(obj=deployment)

    if current_user.is_authenticated and (current_user.is_active and (current_user.admin or
                                          current_user == deployment.user)):
        kwargs['editable'] = True
        if current_user.is_authenticated and (current_user.admin or
                                              current_user.username == deployment.user.username):
            kwargs['admin'] = True

    current_app.logger.info(deployment.dap)
    return render_template('show_deployment.html', form=form,
                           deployment=deployment,
                           username=getattr(current_user, "username", None),
                           files=files, **kwargs)

@deployment_bp.route('/users/<string:username>/deployment/new',
                     methods=['POST'])
@login_required
def new_deployment(username):
    user = User.query.filter_by(username=username).one_or_none()
    if user is None or (user is not None and not current_user.admin and
                        current_user != user):
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for("index.index"))

    form = NewDeploymentForm()

    if form.validate_on_submit():
        deployment_date = dateparse(form.deployment_date.data)
        delayed_mode = form.delayed_mode.data
        deployment_name = form.glider_name.data + '-' + \
            deployment_date.strftime('%Y%m%dT%H%M')
        if delayed_mode:
            deployment_name += '-delayed'

        try:
            # TODO: should this be handled at SQLAlchemy level?
            existing_deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()
            if existing_deployment is not None:
                # TODO: Raise more appropriate exception?
                raise ValueError("Duplicate Key Detected: name")
            # TODO: Consolidate logic
            existing_deployment = Deployment.query.filter_by(glider_name=form.glider_name.data,
                                                                deployment_date=deployment_date).one_or_none()
            if existing_deployment is not None:
                # if there is a previous real-time deployment and the one
                # to create is marked as delayed mode, act as if the delayed
                # mode modification path had been followed
                if not existing_deployment.delayed_mode and delayed_mode:
                    return new_delayed_mode_deployment(username,
                                                       existing_deployment._id)
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
            flash("Deployment created", 'success')
            send_registration_email(deployment.user.username, deployment)
        # TODO: handle prior to creation
        #except DuplicateKeyError:
        except Exception as e:
            raise(e)
            flash("Deployment names must be unique across Glider DAC: %s already used" %
                  deployment_name, 'danger')

    else:
        error_str = ", ".join(["%s: %s" % (k, ", ".join(v))
                               for k, v in form.errors.items()])
        flash("Deployment could not be created: %s" % error_str, 'danger')

    return redirect(url_for('deployment.list_user_deployments',
                            username=username))


@deployment_bp.route('/users/<string:username>/deployment/<string:deployment_name>/new',
           methods=['POST'])
@login_required
def new_delayed_mode_deployment(username, deployment_name):
    '''
    Endpoint for submitting a delayed mode deployment from an existing
    realtime deployment

    :param string username: Username
    :param str deployment_name: Name of the existing realtime deployment
    '''
    user = User.query.filter_by(username=username).one_or_none()
    if user is None or (user is not None and not current_user.admin and
                        current_user != user):
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for("index.index"))

    rt_deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()
    # Need to check if the "real time" deployment is complete yet
    if not rt_deployment.completed:
        deployment_url = url_for('deployment.show_deployment', username=username, deployment_name=deployment_name)
        flash('The real time %s must be marked as complete before adding delayed mode data' %
              rt_deployment.name, 'danger')
        return redirect(url_for('deployment.list_user_deployments', username=username))

    deployment = Deployment()
    deployment.name = rt_deployment.name + '-delayed'
    #deployment.user_id = user.user_id
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
    flash("Deployment created", 'success')
    send_registration_email(deployment.user.username, deployment)

    return redirect(url_for('deployment.list_user_deployments', username=username))

@deployment_bp.route('/users/<string:username>/deployment/<string:deployment_name>/edit', methods=['POST'])
@login_required
def edit_deployment(username, deployment_name):

    user = User.query.filter_by(username=username).one_or_none()
    if user is None or (user is not None and not current_user.admin and
                        current_user != user):
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for('deployment.list_user_deployments', username=username))

    deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()

    form = DeploymentForm(obj=deployment)

    if form.validate_on_submit():
        form.populate_obj(deployment)
        deployment.updated = datetime.utcnow()
        db.session.commit()
        flash("Deployment updated", 'success')
        return redirect(url_for('deployment.show_deployment', username=username, deployment_name=deployment.name))
    else:
        error_str = ", ".join(["%s: %s" % (k, ", ".join(v))
                               for k, v in form.errors.items()])
        flash("Deployment could not be edited: %s" % error_str, 'danger')

    return render_template('edit_deployment.html', username=username, form=form, deployment=deployment)


@deployment_bp.route('/users/<string:username>/deployment/<string:deployment_name>/files', methods=['POST'])
@login_required
def post_deployment_file(username, deployment_name):

    deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()
    user = User.query.filter_by(username=username).one_or_none()

    if not (deployment and user and deployment.user.username == user.username and
            (current_user.admin or current_user == user)):
        raise Exception("Unauthorized")  # @TODO better response via ajax?

    retval = []
    for name, f in request.files.items():
        if not name.startswith('file-'):
            continue

        safe_filename = f.filename  # @TODO

        out_name = os.path.join(deployment.full_path, safe_filename)

        try:
            with open(out_name, 'wb') as of:
                f.save(of)
        except Exception:
            current_app.logger.exception('Error uploading file: {}'.format(out_name))

        retval.append((safe_filename, datetime.utcnow()))
    editable = current_user and current_user.is_active and (
        current_user.admin or current_user == user)

    return render_template("_deployment_files.html", files=retval, editable=editable)


@deployment_bp.route('/users/<string:username>/deployment/<string:deployment_name>/delete_files', methods=['POST'])
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
    if not (current_user and current_user.is_active and (current_user.admin
                                                         or current_user ==
                                                         user)):
        # @TODO better response via ajax?
        raise Exception("Unauthorized")

    if not (deployment and user and (current_user.admin or user._id ==
                                     deployment.user_id)):
        # @TODO better response via ajax?
        raise Exception("Unauthorized")

    for name in request.json['files']:
        file_name = os.path.join(deployment.full_path, name)
        os.unlink(file_name)

    return ""


@deployment_bp.route('/users/<string:username>/deployment/<string:deployment_name>/delete', methods=['POST'])
@login_required
def delete_deployment(username, deployment_name):

    deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()
    user = User.query.filter_by(username=username).one_or_none()
    if deployment is None:
        flash("Permission denied", 'danger')
        return redirect(url_for("deployment.show_deployment", username=username, deployment_name=deployment_name))
    if user is None:
        flash("Permission denied", 'danger')
        return redirect(url_for("deployment.show_deployment", username=username, deployment_name=deployment_name))
    if not (current_user and current_user.is_active and (current_user.admin
                                                         or current_user ==
                                                         user)):
        flash("Permission denied", 'danger')
        return redirect(url_for("deployment.show_deployment", username=username, deployment_name=deployment_name))

    # TODO: consider moving back to task queue?
    deployment.delete_deployment()
    flash("Deployment and associated files deleted", "success")

    return redirect(url_for("deployment.list_user_deployments", username=username))


# TODO: Is this method even needed anymore?
@deployment_bp.route('/api/deployment', methods=['GET'])
@cross_origin()
def get_deployments():
    '''
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
    '''
    # Parse case insensitive query parameters
    request_query = CIMultiDict(request.args)
    query = Deployment.query.with_entities(Deployment.name,
                                           Deployment.operator,
                                           Deployment.deployment_dir,
                                           Deployment.wmo_id,
                                           Deployment.attribution,
                                           Deployment.completed,
                                           Deployment.created,
                                           Deployment.updated,
                                           Deployment.glider_name,
                                           Deployment.archive_safe,
                                           Deployment.checksum,
                                           Deployment.delayed_mode,
                                           Deployment.latest_file,
                                           Deployment.latest_file_mtime,
                                           Deployment.compliance_check_pass)
                                           #Deployment.dap,
                                           #Deployment.sos,
                                           #Deployment.iso,
                                           #Deployment.erddap,
                                           #Deployment.thredds)

    def parse_date(datestr):
        '''
        Parse the time query param
        '''
        try:
            if datestr.startswith('now-'):
                p = re.compile(r'^now-(?P<val>\d+)\s*(?P<units>\w+)$')
                match = p.search(datestr)
                val = int(match.group('val'))
                units = match.group('units')
                # If not valid units, exception will throw
                unknown_unit = Unit(units)
                hrs = Unit('hours')
                # convert to hours
                num_hrs = unknown_unit.convert(val, hrs)
                dt_now = datetime.now(tz=timezone.utc)
                return dt_now - timedelta(hours=num_hrs)

            return dateparse(datestr)
        except Exception:
            return None

    # Get the query values
    completed = request_query.get('completed', None)
    if completed and completed.lower() in {'true', 'false'}:
        is_completed = True if completed.lower() == 'true' else False
        query = query.filter(Deployment.completed == is_completed)
    delayed_mode = request_query.get('delayed_mode', None)
    if delayed_mode and delayed_mode.lower() in {'true', 'false'}:
        is_delayed_mode = True if delayed_mode.lower() == 'true' else False
        query = query.filter(Deployment.delayed_mode == is_delayed_mode)
    min_time = request_query.get('minTime', None)
    if min_time:
        min_time_dt = parse_date(min_time)
        query = query.filter(Deployment.latest_file_mtime >= min_time_dt)

    deployments = query.all()
    deployment_schema = DeploymentSchema()

    deployment_results = []
    #deployment_results = deployment_schema.dump(deployments)
    for deployment in deployments:
        deployment_info = deployment_schema.dump(deployment)
        deployment_results.append(deployment_info)
    return jsonify(deployment_results)


@deployment_bp.route('/api/deployment/<string:username>/<string:deployment_name>', methods=['GET'])
@cross_origin()
def get_deployment(username, deployment_name):
    deployment = Deployment.query.filter_by(username=username,
                                            name=deployment_name).one_or_none()
    if deployment is None:
        return jsonify(message='No record found'), 204
    d = json.loads(deployment.to_json())
    d['id'] = d['_id']['$oid']
    del d['_id']
    del d['user_id']
    d['sos'] = deployment.sos
    d['iso'] = deployment.iso
    d['dap'] = deployment.dap
    d['erddap'] = deployment.erddap
    d['thredds'] = deployment.thredds
    d['attribution'] = deployment.attribution
    return jsonify(**d)
