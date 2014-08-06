import os
import os.path
from datetime import datetime

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from flask_login import login_required, current_user
from glider_dac import app, db
from glider_dac.models.user import User

from flask_wtf import Form
from wtforms import validators, TextField, PasswordField, SubmitField
from wtforms.form import BaseForm

class UserForm(Form):
    username        = TextField(u'Username')
    name            = TextField(u'Name')
    password        = PasswordField('Password', [
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm         = PasswordField('Confirm Password')
    organization    = TextField(u'Organization')
    email           = TextField(u'Email')
    submit          = SubmitField("Submit")

@login_required
@app.route('/users/<string:username>', methods=['GET', 'POST'])
def edit_user(username):
    user = db.User.find_one( {'username' : username } )
    if user is None or (user is not None and not current_user.is_admin() and current_user != user):
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for("index"))

    form = UserForm(obj=user)

    if form.validate_on_submit():
        form.populate_obj(user)
        user.save()
        if form.password.data:
            User.update(username=user.username, password=form.password.data)
        flash("Account updated", 'success')
        return redirect(url_for("index"))

    return render_template('edit_user.html', form=form, user=user)

@login_required
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not current_user.is_admin():
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for("index"))

    form = UserForm()

    if form.is_submitted() and BaseForm.validate(form, extra_validators={'password':[validators.Required()]}):
        user = db.User()
        form.populate_obj(user)
        user.save()
        User.update(username=user.username, password=form.password.data)

        # make sure user dirs exist
        user.ensure_dir('upload')

        flash("Account for '%s' created" % user.username, 'success')
        return redirect(url_for("admin"))

    users = db.User.find()

    deployment_counts_raw = db.User.get_deployment_count_by_user()
    deployment_counts = {m['_id']:m['count'] for m in deployment_counts_raw}

    return render_template('admin.html', form=form, users=users, deployment_counts=deployment_counts)

@login_required
@app.route('/admin/<ObjectId:user_id>', methods=['GET', 'POST'])
def admin_edit_user(user_id):
    user = db.User.find_one({'_id':user_id})

    if not current_user.is_admin():
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for("index"))

    form = UserForm(obj=user)

    if form.validate_on_submit():
        form.populate_obj(user)
        user.save()
        if form.password.data:
            User.update(username=user.username, password=form.password.data)
        flash("Account updated", 'success')
        return redirect(url_for("admin"))

    return render_template('edit_user.html', form=form, user=user)

@login_required
@app.route('/admin/<ObjectId:user_id>/delete', methods=['POST'])
def admin_delete_user(user_id):
    user = db.User.find_one({'_id':user_id})

    if not current_user.is_admin():
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for("index"))

    if user._id == current_user._id:
        flash("You can't delete yourself!", "danger")
        return redirect(url_for("admin"))

    user.delete()

    flash("User deleted", "success")
    return redirect(url_for('admin'))

