#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
glider_dac/views/deployment.py
View definition for Deployments
'''
from datetime import datetime
from flask import render_template, redirect, jsonify, flash, url_for, request, Markup
from flask_login import login_required, current_user
from flask_cors import cross_origin
from glider_dac import app, db, queue
from glider_dac.glider_emails import send_registration_email
from glider_dac import tasks

from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField, BooleanField, validators
from pymongo.errors import DuplicateKeyError
from dateutil.parser import parse as dateparse
import re
import json
import os
import os.path


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
    operator = TextField('Operator')
    completed = BooleanField('Completed')
    archive_safe = BooleanField("Submit to NCEI on Completion")
    attribution = TextField('Attribution')
    submit = SubmitField('Submit')


class NewDeploymentForm(FlaskForm):
    glider_name = TextField('Glider Name', [is_valid_glider_name])
    deployment_date = TextField('Deployment Date', [is_date_parseable])
    attribution = TextField('Attribution')
    delayed_mode = BooleanField('Delayed Mode?')
    submit = SubmitField("Create")

@app.route('/users/<string:username>/deployments')
def list_user_deployments(username):
    user = db.User.find_one({'username': username})
    deployments = list(db.Deployment.find({'user_id': user._id}))

    kwargs = {}
    if current_user and current_user.is_active and (current_user.is_admin or
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


@app.route('/operators/<path:operator>/deployments')
def list_operator_deployments(operator):
    deployments = list(db.Deployment.find({'operator': str(operator)}))

    for m in deployments:
        if not os.path.exists(m.full_path):
            continue

        m.updated = datetime.utcfromtimestamp(os.path.getmtime(m.full_path))

    deployments.sort(key=deployment_key_fn)

    return render_template('operator_deployments.html', operator=operator, deployments=deployments)


@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>')
def show_deployment(username, deployment_id):
    user = db.User.find_one({'username': username})
    deployment = db.Deployment.find_one({'_id': deployment_id})

    files = []
    for dirpath, dirnames, filenames in os.walk(deployment.full_path):
        for f in filenames:
            if f in ["deployment.json", "wmoid.txt", "completed.txt"] or f.endswith(".md5"):
                continue
            files.append((f, datetime.utcfromtimestamp(
                os.path.getmtime(os.path.join(dirpath, f)))))

    files.sort(key=lambda a: a[1])

    kwargs = {}

    form = DeploymentForm(obj=deployment)

    if current_user and current_user.is_active and (current_user.is_admin or
                                                    current_user == user):
        kwargs['editable'] = True
        if current_user.is_admin or current_user == user:
            kwargs['admin'] = True

    return render_template('show_deployment.html', username=username, form=form, deployment=deployment, files=files, **kwargs)


@app.route('/deployment/<ObjectId:deployment_id>')
def show_deployment_no_username(deployment_id):
    deployment = db.Deployment.find_one({'_id': deployment_id})
    username = db.User.find_one({'_id': deployment.user_id}).username
    return redirect(url_for('show_deployment', username=username, deployment_id=deployment._id))


@app.route('/users/<string:username>/deployment/new', methods=['POST'])
@login_required
def new_deployment(username):
    user = db.User.find_one({'username': username})
    if user is None or (user is not None and not current_user.is_admin and
                        current_user != user):
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for("index"))

    form = NewDeploymentForm()

    if form.validate_on_submit():
        deployment_date = dateparse(form.deployment_date.data)
        delayed_mode = form.delayed_mode.data
        deployment_name = form.glider_name.data + '-' + \
            deployment_date.strftime('%Y%m%dT%H%M')
        if delayed_mode:
            deployment_name += '-delayed'

        deployment = db.Deployment()
        # form.populate_obj(deployment)
        deployment.user_id = user._id
        deployment.username = username
        deployment.deployment_dir = os.path.join(username, deployment_name)
        deployment.updated = datetime.utcnow()
        deployment.deployment_date = deployment_date
        deployment.glider_name = form.glider_name.data
        deployment.name = deployment_name
        deployment.attribution = form.attribution.data
        deployment.delayed_mode = delayed_mode
        try:
            existing_deployment = db.Deployment.find_one(
                {'name': deployment_name})
            if existing_deployment is not None:
                raise DuplicateKeyError("Duplicate Key Detected: name")
            existing_deployment = db.Deployment.find_one(
                {'glider_name': form.glider_name.data, 'deployment_date': deployment_date})
            if existing_deployment is not None:
                raise DuplicateKeyError(
                    "Duplicate Key Detected: glider_name and deployment_date")
            deployment.save()
            flash("Deployment created", 'success')
            send_registration_email(username, deployment)
        except DuplicateKeyError:
            flash("Deployment names must be unique across Glider DAC: %s already used" %
                  deployment.name, 'danger')

    else:
        error_str = ", ".join(["%s: %s" % (k, ", ".join(v))
                               for k, v in form.errors.items()])
        flash("Deployment could not be created: %s" % error_str, 'danger')

    return redirect(url_for('list_user_deployments', username=username))


@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>/new', methods=['POST'])
@login_required
def new_delayed_mode_deployment(username, deployment_id):
    '''
    Endpoint for submitting a delayed mode deployment from an existing
    realtime deployment

    :param string username: Username
    :param ObjectId deployment_id: Id of the existing realtime deployment
    '''
    user = db.User.find_one({'username': username})
    if user is None or (user is not None and not current_user.is_admin and
                        current_user != user):
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for("index"))

    rt_deployment = db.Deployment.find_one({'_id': deployment_id})
    # Need to check if the "real time" deployment is complete yet
    if not rt_deployment.completed:
        deployment_url = url_for('show_deployment', username=username, deployment_id=deployment_id)
        flash(Markup('The real time deployment <a href="%s">%s</a> must be marked as complete before adding delayed mode data' %
              (deployment_url, rt_deployment.name)), 'danger')
        return redirect(url_for('list_user_deployments', username=username))

    deployment = db.Deployment()
    deployment_name = rt_deployment.name + '-delayed'
    deployment.name = deployment_name
    deployment.user_id = user._id
    deployment.username = username
    deployment.operator = rt_deployment.operator
    deployment.deployment_dir = os.path.join(username, deployment_name)
    deployment.wmo_id = rt_deployment.wmo_id
    deployment.updated = datetime.utcnow()
    deployment.glider_name = rt_deployment.glider_name
    deployment.deployment_date = rt_deployment.deployment_date
    deployment.attribution = rt_deployment.attribution
    deployment.delayed_mode = True
    try:
        existing_deployment = db.Deployment.find_one(
            {'name': deployment_name})
        if existing_deployment is not None:
            raise DuplicateKeyError("Duplicate Key Detected: name")
        deployment.save()
        flash("Deployment created", 'success')
        send_registration_email(username, deployment)
    except DuplicateKeyError:
        flash("Deployment names must be unique across Glider DAC: %s already used" %
              deployment.name, 'danger')

    return redirect(url_for('list_user_deployments', username=username))

@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>/edit', methods=['POST'])
@login_required
def edit_deployment(username, deployment_id):

    user = db.User.find_one({'username': username})
    if user is None or (user is not None and not current_user.is_admin and
                        current_user != user):
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for('list_user_deployments', username=username))

    deployment = db.Deployment.find_one({'_id': deployment_id})

    form = DeploymentForm(obj=deployment)

    if form.validate_on_submit():
        form.populate_obj(deployment)
        deployment.updated = datetime.utcnow()
        deployment.save()
        flash("Deployment updated", 'success')
        return redirect(url_for('show_deployment', username=username, deployment_id=deployment._id))
    else:
        error_str = ", ".join(["%s: %s" % (k, ", ".join(v))
                               for k, v in form.errors.items()])
        flash("Deployment could not be edited: %s" % error_str, 'danger')

    return render_template('edit_deployment.html', username=username, form=form, deployment=deployment)


@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>/files', methods=['POST'])
@login_required
def post_deployment_file(username, deployment_id):

    deployment = db.Deployment.find_one({'_id': deployment_id})
    user = db.User.find_one({'username': username})

    if not (deployment and user and deployment.user_id == user._id and
            (current_user.is_admin or current_user == user)):
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
        # TODO: add logging
        except OSError:
            pass
        except:
            pass

        retval.append((safe_filename, datetime.utcnow()))

    editable = current_user and current_user.is_active and (
        current_user.is_admin or current_user == user)

    return render_template("_deployment_files.html", files=retval, editable=editable)


@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>/delete_files', methods=['POST'])
@login_required
def delete_deployment_files(username, deployment_id):

    deployment = db.Deployment.find_one({'_id': deployment_id})
    user = db.User.find_one({'username': username})
    if deployment is None:
        # @TODO better response via ajax?
        raise Exception("Unauthorized")
    if user is None:
        # @TODO better response via ajax?
        raise Exception("Unauthorized")
    if not (current_user and current_user.is_active and (current_user.is_admin
                                                         or current_user ==
                                                         user)):
        # @TODO better response via ajax?
        raise Exception("Unauthorized")

    if not (deployment and user and (current_user.is_admin or user._id ==
                                     deployment.user_id)):
        # @TODO better response via ajax?
        raise Exception("Unauthorized")

    for name in request.json['files']:
        file_name = os.path.join(deployment.full_path, name)
        os.unlink(file_name)

    return ""


@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>/delete', methods=['POST'])
@login_required
def delete_deployment(username, deployment_id):

    deployment = db.Deployment.find_one({'_id': deployment_id})
    user = db.User.find_one({'username': username})
    if deployment is None:
        flash("Permission denied", 'danger')
        return redirect(url_for("show_deployment", username=username, deployment_id=deployment_id))
    if user is None:
        flash("Permission denied", 'danger')
        return redirect(url_for("show_deployment", username=username, deployment_id=deployment_id))
    if not (current_user and current_user.is_active and (current_user.is_admin
                                                         or current_user ==
                                                         user)):
        flash("Permission denied", 'danger')
        return redirect(url_for("show_deployment", username=username, deployment_id=deployment_id))

    queue.enqueue_call(func=tasks.delete_deployment,
                       args=(deployment_id,), timeout=30)
    flash("Deployment queued for deletion", 'success')

    return redirect(url_for("list_user_deployments", username=username))


@app.route('/api/deployment', methods=['GET'])
@cross_origin()
def get_deployments():
    deployments = db.Deployment.find()
    results = []
    for deployment in deployments:
        d = json.loads(deployment.to_json())
        d['id'] = d['_id']['$oid']
        del d['_id']
        del d['user_id']
        d.pop('compliance_check_report', None)
        d['sos'] = deployment.sos
        d['iso'] = deployment.iso
        d['dap'] = deployment.dap
        d['erddap'] = deployment.erddap
        d['thredds'] = deployment.thredds
        d['attribution'] = deployment.attribution
        results.append(d)

    return jsonify(results=results, num_results=len(results))


@app.route('/api/deployment/<string:username>/<string:deployment_name>', methods=['GET'])
@cross_origin()
def get_deployment(username, deployment_name):
    deployment = db.Deployment.find_one(
        {"username": username, "name": deployment_name})
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
