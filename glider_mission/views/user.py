import os
import os.path
from datetime import datetime

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from flask_login import login_required, current_user
from glider_mission import app, db

from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, SubmitField

class UserForm(Form):
    name = TextField(u'Name')
    organization = TextField(u'Organization')
    email = TextField(u'Email')
    submit = SubmitField("Edit")

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
        flash("Account updated")
        return redirect(url_for("index"))

    return render_template('edit_user.html', form=form, user=user)
