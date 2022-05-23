#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
glider_dac/views/index.py
'''
from bson.objectid import ObjectId
from flask import render_template, make_response, redirect, flash, url_for, request
from flask import current_app
from glider_dac import login_manager, db
from glider_dac.models.user import User
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
import pymongo


class LoginForm(FlaskForm):
    username = StringField('Name')
    password = PasswordField('Password')


@app.route('/', methods=['GET'])
def index():
    deployments = list(db.Deployment.find(
        sort=[("created", pymongo.DESCENDING)], limit=20))

    user_deployments = db.User.get_deployment_count_by_user()
    user_map = {u._id: u for u in db.User.find()}

    operator_deployments = db.Deployment.get_deployment_count_by_operator()

    return render_template('index.html',
                           deployments=deployments,
                           user_deployments=user_deployments,
                           user_map=user_map,
                           operator_deployments=operator_deployments)


@login_manager.user_loader
def load_user(userid):
    return db.User.find_one({"_id": ObjectId(userid)})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_active:
        flash("Already logged in", 'warning')
        return redirect(request.args.get("next") or url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if not user:
            flash("Failed", 'danger')
            return redirect(url_for("login"))

        login_user(user)
        flash("Logged in successfully", 'success')
        return redirect(request.args.get("next") or url_for("index"))
    response = make_response(render_template("login.html", form=form))
    return response


@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for("index"))


def serialize_date(date):
    if date is not None:
        return date.isoformat()


@app.route('/crossdomain.xml', methods=['GET'])
def crossdomain():
    domain = """
    <cross-domain-policy>
        <allow-access-from domain="*"/>
        <site-control permitted-cross-domain-policies="all"/>
        <allow-http-request-headers-from domain="*" headers="*"/>
    </cross-domain-policy>
    """
    response = make_response(domain)
    response.headers["Content-type"] = "text/xml"
    return response
