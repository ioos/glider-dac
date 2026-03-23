#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
glider_dac/views/index.py
"""

from flask import (
    jsonify,
    render_template,
    make_response,
    redirect,
    flash,
    url_for,
    request,
    current_app,
    Blueprint)

from glider_dac.models.institution import Institution
from glider_dac.models.user import User
from glider_dac.models.deployment import Deployment
from glider_dac.extensions import db
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm
from sqlalchemy import select, func
from wtforms import StringField, PasswordField

index_bp = Blueprint("index", __name__)

def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


class LoginForm(FlaskForm):
    username = StringField("Name")
    password = PasswordField("Password")


@index_bp.route("/", methods=["GET"])
def index():
    name_filter = request.args.get("name")
    wmo_id_filter = request.args.get("wmo_id")
    base_query = Deployment.query
    if name_filter:
        # Consider optimizing if like query becomes too slow.
        # Probably OK for small number of deployments.
        base_query = base_query.filter(Deployment.name.ilike(f"%{name_filter}%"))
    if wmo_id_filter:
        base_query = base_query.filter(Deployment.wmo_id == wmo_id_filter)

    deployments = base_query.order_by(Deployment.created.desc()).limit(20)

    user_deployments = (
        db.session.query(User.name, func.count(Deployment.name))
        .join(Deployment, Deployment.user_id == User.id)
        .filter(Deployment.id.in_(base_query.with_entities(Deployment.id)))
        .group_by(User.name)
        .all()
    )

    operator_deployments = (
        db.session.query(Deployment.operator, func.count())
        .filter(Deployment.id.in_(base_query.with_entities(Deployment.id)))
        .group_by(Deployment.operator)
        .all()
    )

    return render_template(
        "index.html",
        deployments=deployments,
        user_deployments=user_deployments,
        operator_deployments=operator_deployments,
    )


@index_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_active:
        flash("Already logged in", "warning")
        return redirect(request.args.get("next") or url_for("index.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if not user:
            flash("Failed", "danger")
            return redirect(url_for("index.login"))

        login_user(user)
        flash("Logged in successfully", "success")
        return redirect(request.args.get("next") or url_for("index.index"))
    response = make_response(render_template("login.html", form=form))
    return response


@index_bp.route("/logout", methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for("index.index"))


def serialize_date(date):
    if date is not None:
        return date.isoformat()


@index_bp.route("/site-map")
def site_map():
    """
    Returns a json structure for the site routes and handlers
    """
    links = []
    for rule in current_app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint)
            links.append((url, rule.endpoint))
    # links is now a list of url, endpoint tuples
    return jsonify(rules=links)


@index_bp.route("/crossdomain.xml", methods=["GET"])
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
