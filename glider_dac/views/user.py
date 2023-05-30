#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
glider_dac/views/user.py
View definitions for Users
'''
from flask import render_template, redirect, flash, url_for, request
from flask_login import login_required, current_user
from glider_dac import app, db
from glider_dac.models.user import User
from flask_wtf import FlaskForm
from wtforms import validators, StringField, PasswordField, SubmitField
from wtforms.form import BaseForm


class UserForm(FlaskForm):
    username = StringField('Username')
    name = StringField('Name')
    password = PasswordField('Password', [
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')
    organization = StringField('Organization')
    email = StringField('Email')
    submit = SubmitField("Submit")


@app.route('/users/<string:username>', methods=['GET', 'POST'])
@login_required
def edit_user(username):
    app.logger.info("GET %s", username)
    app.logger.info("Request URL: %s", request.url)
    user = db.User.find_one({'username': username})
    if user is None or (user is not None and not current_user.is_admin and current_user != user):
        # No permission
        app.logger.error("Permission is denied")
        app.logger.error("User: %s", user)
        app.logger.error("Admin?: %s", current_user.is_admin)
        app.logger.error("Not current user?: %s", current_user != user)
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


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for("index"))

    form = UserForm()

    if (form.is_submitted() and
        BaseForm.validate(form,
                          extra_validators={'password':
                                            [validators.InputRequired()]})):
        user = db.User()
        form.populate_obj(user)
        user.save()
        User.update(username=user.username, password=form.password.data)

        flash("Account for '%s' created" % user.username, 'success')
        return redirect(url_for("admin"))

    users = db.User.find()

    deployment_counts_raw = db.User.get_deployment_count_by_user()
    deployment_counts = {m['_id']: m['count'] for m in deployment_counts_raw}

    return render_template('admin.html', form=form, users=users, deployment_counts=deployment_counts)


@app.route('/admin/<ObjectId:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    user = db.User.find_one({'_id': user_id})

    if not current_user.is_admin:
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


@app.route('/admin/<ObjectId:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    user = db.User.find_one({'_id': user_id})

    if not current_user.is_admin:
        # No permission
        flash("Permission denied", 'danger')
        return redirect(url_for("index"))

    if user._id == current_user._id:
        flash("You can't delete yourself!", "danger")
        return redirect(url_for("admin"))

    user.delete()

    flash("User deleted", "success")
    return redirect(url_for('admin'))
