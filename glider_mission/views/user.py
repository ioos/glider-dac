import os
import os.path
from datetime import datetime

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from flask_login import login_required, current_user
from glider_mission import app, db

from flask_wtf import Form
from wtforms import validators, TextField, PasswordField, SubmitField

class UserForm(Form):
    name            = TextField(u'Name')
    password        = PasswordField('Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm         = PasswordField('Confirm Password')
    organization    = TextField(u'Organization')
    email           = TextField(u'Email')
    submit          = SubmitField("Submit")

class NewUserForm(Form):
    username        = TextField(u'Username')
    password        = PasswordField('Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm         = PasswordField('Confirm Password')
    name            = TextField(u'Name')
    organization    = TextField(u'Organization')
    email           = TextField(u'Email')
    submit          = SubmitField(u'Create')

@login_required
@app.route('/users/<string:username>', methods=['GET', 'POST'])
def edit_user(username):
    user = db.User.find_one( {'username' : username } )
    if user is None or (user is not None and not current_user.is_admin() and current_user != user):
        # No permission
        flash("Permission denied")
        return redirect(url_for("index"))

    form = UserForm(obj=user)

    if form.validate_on_submit():
        form.populate_obj(user)
        user.save()
        User.update(username=user.username, password=form.password.data)
        flash("Account updated")
        return redirect(url_for("index"))

    return render_template('edit_user.html', form=form, user=user)

@login_required
@app.route('/user/create', methods=['POST'])
def create_user():
    if not current_user.is_admin():
        # No permission
        flash("Permission denied")
        return redirect(url_for("index"))

    form = NewUserForm()

    if form.validate_on_submit():
        user = db.User()
        form.populate_obj(user)
        user.save()
        User.update(username=user.username, password=form.password.data)
        flash("Account for '%s' created" % user.username)
        return redirect(url_for("admin"))

    return render_template('admin.html', form=form)

@login_required
@app.route('/admin', methods=['GET'])
def admin():
    if not current_user.is_admin():
        # No permission
        flash("Permission denied")
        return redirect(url_for("index"))

    form = NewUserForm()

    return render_template('admin.html', form=form)


