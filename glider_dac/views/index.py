#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
glider_dac/views/index.py
'''
from flask import (render_template, make_response, redirect, flash, url_for,
                   request, current_app, Blueprint)
#from flask import current_app
from glider_dac.models.user import User
from glider_dac.models.deployment import Deployment
from glider_dac.models.user import User
from glider_dac.extensions import db
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm
from sqlalchemy import select, func
from wtforms import StringField, PasswordField

index_bp = Blueprint("index", __name__)

class LoginForm(FlaskForm):
    username = StringField('Name')
    password = PasswordField('Password')


@index_bp.route('/', methods=['GET'])
def index():
    deployments = Deployment.query.order_by(Deployment.created.desc()).limit(20)
    user_deployments = (db.session.execute(select(User.name,
                                 func.count(Deployment.user_id)).join(User)
                                 .group_by(Deployment.user_id)).all())

    operator_deployments = (db.session.execute(
                                    select(Deployment.operator, func.count())
                                    .group_by(Deployment.operator)).all())

    return render_template('index.html',
                           deployments=deployments,
                           user_deployments=user_deployments,
                           operator_deployments=operator_deployments)


@index_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_active:
        flash("Already logged in", 'warning')
        return redirect(request.args.get("next") or url_for("index.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if not user:
            flash("Failed", 'danger')
            return redirect(url_for("index.login"))

        login_user(user)
        flash("Logged in successfully", 'success')
        return redirect(request.args.get("next") or url_for("index.index"))
    response = make_response(render_template("login.html", form=form))
    return response


@index_bp.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for("index.index"))


def serialize_date(date):
    if date is not None:
        return date.isoformat()


@index_bp.route('/site-map')
def site_map():
    '''
    Returns a json structure for the site routes and handlers
    '''
    links = []
    for rule in current_app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint)
            links.append((url, rule.endpoint))
    # links is now a list of url, endpoint tuples
    return jsonify(rules=links)


@index_bp.route('/crossdomain.xml', methods=['GET'])
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
