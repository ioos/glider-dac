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
from dateutil.parser import parse as dateparse
import re

def is_date_parseable(form, field):
    try:
        dateobj = dateparse(field.data)
    except ValueError:
        raise validators.ValidationError("Invalid Date")

def is_valid_glider_name(form, field):
    regex = ur'^[a-zA-Z]+[a-zA-Z0-9-_]*$'
    if not re.match(regex, field.data):
        raise validators.ValidationError("Invalid Glider Name")


class DeploymentForm(Form):
    operator                    = TextField(u'Operator')
    wmo_id                      = TextField(u'WMO ID')
    completed                   = BooleanField(u'Completed')
    submit                      = SubmitField(u'Submit')

class NewDeploymentForm(Form):
    glider_name     = TextField(u'Glider Name', [is_valid_glider_name])
    deployment_date = TextField(u'Deployment Date', [is_date_parseable])
    wmo_id          = TextField(u'WMO ID')
    submit          = SubmitField(u"Create")

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
        if not os.path.exists(m.full_path):   # wat
            continue

        m.updated = datetime.utcfromtimestamp(os.path.getmtime(m.full_path))

    deployments = sorted(deployments, lambda a, b: cmp(b.updated, a.updated))

    return render_template('user_deployments.html', username=username, deployments=deployments, **kwargs)

@app.route('/operators/<string:operator>/deployments')
def list_operator_deployments(operator):
    deployments = list(db.Deployment.find( { 'operator' : unicode(operator) } ))

    for m in deployments:
        if not os.path.exists(m.full_path):
            continue

        m.updated = datetime.utcfromtimestamp(os.path.getmtime(m.full_path))

    deployments = sorted(deployments, lambda a, b: cmp(b.updated, a.updated))

    return render_template('operator_deployments.html', operator=operator, deployments=deployments)

@app.route('/users/<string:username>/deployment/<ObjectId:deployment_id>')
def show_deployment(username, deployment_id):
    user = db.User.find_one( {'username' : username } )
    deployment = db.Deployment.find_one({'_id':deployment_id})

    files = []
    for dirpath, dirnames, filenames in os.walk(deployment.full_path):
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


    if form.validate_on_submit():
        deployment_date = dateparse(form.deployment_date.data)
        deployment_name = form.glider_name.data + '-' + deployment_date.strftime('%Y%m%dT%H%M')

        upload_root = user.data_root
        new_deployment_dir = os.path.join(upload_root, deployment_name)

        deployment = db.Deployment()
        #form.populate_obj(deployment)
        deployment.user_id = user._id
        deployment.username = username
        deployment.deployment_dir = os.path.join(username, deployment_name)
        deployment.updated = datetime.utcnow()
        deployment.deployment_date = deployment_date
        deployment.glider_name = form.glider_name.data
        deployment.name = deployment_name
        try:
            existing_deployment = db.Deployment.find_one({'name' : deployment_name})
            if existing_deployment is not None:
                raise DuplicateKeyError("Duplicate Key Detected: name")
            existing_deployment = db.Deployment.find_one({'glider_name' : form.glider_name.data, 'deployment_date':deployment_date})
            if existing_deployment is not None:
                raise DuplicateKeyError("Duplicate Key Detected: glider_name and deployment_date")
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

        out_name = os.path.join(deployment.full_path, safe_filename)

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
        file_name = os.path.join(deployment.full_path, name)
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

    shutil.rmtree(deployment.full_path)
    deployment.delete()

    return redirect(url_for("list_user_deployments", username=username))

@app.route('/api/deployment', methods=['GET'])
def get_deployments():
    deployments = db.Deployment.find()
    results = []
    for deployment in deployments:
        d = json.loads(deployment.to_json())
        d['id'] = d['_id']['$oid']
        del d['_id']
        del d['user_id']
        d['sos'] = deployment.sos
        d['iso'] = deployment.iso
        d['dap'] = deployment.dap
        d['erddap'] = deployment.erddap
        d['thredds'] = deployment.thredds
        results.append(d)

    return jsonify(results=results, num_results=len(results))

@app.route('/api/deployment/<string:username>/<string:deployment_name>', methods=['GET'])
def get_deployment(username, deployment_name):
    deployment = db.Deployment.find_one({"username":username, "name":deployment_name})
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
    return jsonify(**d)

