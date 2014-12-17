import os
import os.path
from datetime import datetime
import json
import shutil
import re

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
from glider_dac import app, db, datetimeformat
from glider_dac.glider_emails import send_wmoid_email

from flask.ext.wtf import Form
from wtforms import TextField, SubmitField, BooleanField, validators
from pymongo.errors import DuplicateKeyError

class DeploymentForm(Form):
    estimated_deploy_date       = TextField(u'Estimated Deploy Date (yyyy-mm-dd)')
    estimated_deploy_location   = TextField(u'Estimated Deploy Location (WKT)')
    operator                    = TextField(u'Operator')
    wmo_id                      = TextField(u'WMO ID')
    completed                   = BooleanField(u'Completed')
    submit                      = SubmitField(u'Submit')

class NewDeploymentForm(Form):
    name    = TextField(u'Deployment Name', [validators.required()])
    wmo_id  = TextField(u'WMO ID')
    submit  = SubmitField(u"Create")

@app.route('/users/<string:username>/deployments')
def list_user_deployments(username):
    user = db.User.find_one( {'username' : username } )
    deployments = list(db.Deployment.find( { 'user_id' : user._id } ))

    kwargs = {}
    if current_user and current_user.is_active() and (current_user.is_admin() or current_user == user):
        # Permission to edit
        form = NewDeploymentForm()
        kwargs['form'] = form

    for m in deployments:
        if not os.path.exists(m.deployment_dir):   # wat
            continue

        m.updated = datetime.utcfromtimestamp(os.path.getmtime(m.deployment_dir))

    deployments = sorted(deployments, lambda a, b: cmp(b.updated, a.updated))

    return render_template('user_deployments.html', username=username, deployments=deployments, **kwargs)

@app.route('/operators/<string:operator>/deployments')
def list_operator_deployments(operator):
    deployments = list(db.Deployment.find( { 'operator' : unicode(operator) } ))

    for m in deployments:
        if not os.path.exists(m.deployment_dir):
            continue

        m.updated = datetime.utcfromtimestamp(os.path.getmtime(m.deployment_dir))

    deployments = sorted(deployments, lambda a, b: cmp(b.updated, a.updated))

    return render_template('operator_deployments.html', operator=operator, deployments=deployments)

@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>')
def show_deployment(username, deployment_id):
    user = db.User.find_one( {'username' : username } )
    deployment = db.Deployment.find_one({'_id':deployment_id})

    files = []
    for dirpath, dirnames, filenames in os.walk(deployment.deployment_dir):
        for f in filenames:
            if f in ["deployment.json", "wmoid.txt", "completed.txt"] or f.endswith(".md5"):
                continue
            files.append((f, datetime.utcfromtimestamp(os.path.getmtime(os.path.join(dirpath, f)))))

    files = sorted(files, lambda a,b: cmp(b[1], a[1]))

    kwargs = {}

    form = DeploymentForm(obj=deployment)

    if current_user and current_user.is_active() and (current_user.is_admin() or current_user == user):
        kwargs['editable'] = True
        if current_user.is_admin():
            kwargs['admin'] = True

    return render_template('show_deployment.html', username=username, form=form, deployment=deployment, files=files, **kwargs)

@app.route('/deployment/<ObjectId:deployment_id>')
def show_deployment_no_username(deployment_id):
    deployment = db.Deployment.find_one( { '_id' : deployment_id } )
    username = db.User.find_one( { '_id' : deployment.user_id } ).username
    return redirect(url_for('show_deployment', username=username, deployment_id=deployment._id))

@app.route('/users/<string:username>/deployment/new', methods=['POST'])
@login_required
def new_deployment(username):
    user = db.User.find_one( {'username' : username } )
    if user is None or (user is not None and not current_user.is_admin() and current_user != user):
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for("index"))

    form = NewDeploymentForm()
    bad_regex = r'[^a-zA-z0-9_-]'
    form.name.data = re.sub(bad_regex, '', form.name.data)
    if form.validate_on_submit():

        upload_root = os.path.join(user.data_root, 'upload')
        new_deployment_dir = os.path.join(upload_root, form.name.data)

        deployment = db.Deployment()
        form.populate_obj(deployment)
        deployment.user_id = user._id
        deployment.deployment_dir = new_deployment_dir
        deployment.updated = datetime.utcnow()
        try:
            existing_deployment = db.Deployment.find_one({'name' : form.name.data})
            if existing_deployment is not None:
                raise DuplicateKeyError("Duplicate Key Detected: name")
            deployment.save()
            flash("Deployment created", 'success')
            send_wmoid_email(username, deployment)
        except DuplicateKeyError:
            flash("Deployment names must be unique across Glider DAC: %s already used" % deployment.name, 'danger')

    else:
        error_str = ", ".join(["%s: %s" % (k, ", ".join(v)) for k, v in form.errors.iteritems()])
        flash("Deployment could not be created: %s" % error_str, 'danger')

    return redirect(url_for('list_user_deployments', username=username))


@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>/edit', methods=['POST'])
@login_required
def edit_deployment(username, deployment_id):

    user = db.User.find_one( {'username' : username } )
    if user is None or (user is not None and not current_user.is_admin() and current_user != user):
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for('list_user_deployments', username=username))

    deployment = db.Deployment.find_one({'_id':deployment_id})

    form = DeploymentForm(obj=deployment)

    if form.validate_on_submit():
        form.populate_obj(deployment)
        deployment.updated = datetime.utcnow()
        try:
            deployment.estimated_deploy_date = datetime.strptime(form.estimated_deploy_date.data, "%Y-%m-%d")
        except ValueError:
            deployment.estimated_deploy_date = None
        deployment.save()
        flash("Deployment updated", 'success')
        return redirect(url_for('show_deployment', username=username, deployment_id=deployment._id))
    else:
        error_str = ", ".join(["%s: %s" % (k, ", ".join(v)) for k, v in form.errors.iteritems()])
        flash("Deployment could not be edited: %s" % error_str, 'danger')

    return render_template('edit_deployment.html', username=username, form=form, deployment=deployment)

@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>/files', methods=['POST'])
@login_required
def post_deployment_file(username, deployment_id):

    deployment = db.Deployment.find_one({'_id':deployment_id})
    user = db.User.find_one( {'username' : username } )

    if not (deployment and user and deployment.user_id == user._id and (current_user.is_admin() or current_user == user)):
        raise StandardError("Unauthorized") # @TODO better response via ajax?

    retval = []
    for name, f in request.files.iteritems():
        if not name.startswith('file-'):
            continue

        safe_filename = f.filename # @TODO

        out_name = os.path.join(deployment.deployment_dir, safe_filename)

        with open(out_name, 'w') as of:
            f.save(of)

        retval.append((safe_filename, datetime.utcnow()))

    editable = current_user and current_user.is_active() and (current_user.is_admin() or current_user == user)

    return render_template("_deployment_files.html", files=retval, editable=editable)

@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>/delete_files', methods=['POST'])
@login_required
def delete_deployment_files(username, deployment_id):

    deployment = db.Deployment.find_one({'_id':deployment_id})
    user = db.User.find_one({'username':username})

    if not (deployment and user and (current_user.is_admin() or user._id == deployment.user_id)):
            raise StandardError("Unauthorized")     # @TODO better response via ajax?

    for name in request.json['files']:
        file_name = os.path.join(deployment.deployment_dir, name)
        os.unlink(file_name)

    return ""

@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>/delete', methods=['POST'])
@login_required
def delete_deployment(username, deployment_id):

    deployment = db.Deployment.find_one({'_id':deployment_id})
    user = db.User.find_one( {'username' : username } )

    if not (deployment is not None and user is not None and deployment.user_id == user._id and current_user.is_admin()):
        flash("Permission denied", 'danger')
        return redirect(url_for("show_deployment", username=username, deployment_id=deployment_id))

    shutil.rmtree(deployment.deployment_dir)
    deployment.delete()

    return redirect(url_for("list_user_deployments", username=username))
