#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
glider_dac/views/user.py
View definitions for Users
"""

from flask import (
    render_template,
    redirect,
    flash,
    url_for,
    request,
    Blueprint,
    current_app,
)
from sqlalchemy import func
from flask_login import login_required, current_user
from glider_dac import db
from glider_dac.models.user import User
from flask_wtf import FlaskForm
from glider_dac.models.deployment import Deployment
from wtforms import validators, StringField, PasswordField, SubmitField
from wtforms.form import BaseForm
from flask_security.utils import hash_password


class UserForm(FlaskForm):
    username = StringField("Username")
    name = StringField("Name")
    password = PasswordField(
        "Password", [validators.EqualTo("confirm", message="Passwords must match")]
    )
    confirm = PasswordField("Confirm Password")
    organization = StringField("Organization")
    email = StringField("Email")
    submit = SubmitField("Submit")


user_bp = Blueprint("user", __name__)


@user_bp.route("/users/<string:username>", methods=["GET", "POST"])
@login_required
def edit_user(username):
    current_app.logger.info("GET %s", username)
    current_app.logger.info("Request URL: %s", request.url)
    user = User.query.filter_by(username=username).one_or_none()
    # Compare by username (or id) rather than object identity to avoid cross-session
    # inequality between current_user and a freshly queried user instance.
    if user is None or (
        not current_user.admin and current_user.username != user.username
    ):
        # No permission
        current_app.logger.error("Permission is denied")
        current_app.logger.error("User: %s", user)
        current_app.logger.error("Admin?: %s", current_user.admin)
        current_app.logger.error(
            "Not current user?: %s",
            current_user.username != getattr(user, "username", None),
        )
        flash("Permission denied", "danger")
        return redirect(url_for("index.index"))

    form = UserForm(obj=user)

    if request.method == "POST":
        # Log POST payload to help debug test failures where form fields don't match
        current_app.logger.debug("POST data: %s", dict(request.form))

        if form.validate_on_submit():
            from flask_security.utils import hash_password

            # Prevent populate_obj from overwriting an existing hashed password
            orig_password = user.password
            form.populate_obj(user)

            # Only replace the stored password if a new one was provided; otherwise restore
            if form.password.data:
                user.password = hash_password(form.password.data)
            else:
                user.password = orig_password

            # Ensure user is attached to the session and commit once using Flask-Security idioms
            db.session.add(user)
            db.session.commit()
            flash("Account updated", "success")
            return redirect(url_for("index.index"))
        else:
            # Helpful diagnostics for tests: why the form didn't accept the POST
            current_app.logger.error(
                "User update form failed validation: %s", form.errors
            )
            flash("Please correct the errors in the form", "danger")

    return render_template("edit_user.html", form=form, user=user)


@user_bp.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if not current_user.admin:
        # No permission
        flash("Permission denied", "danger")
        return redirect(url_for("index.index"))

    form = UserForm()

    if form.is_submitted() and BaseForm.validate(
        form, extra_validators={"password": [validators.InputRequired()]}
    ):
        user = User()
        form.populate_obj(user)
        user.password = hash_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("Account for '%s' created" % user.username, "success")
        return redirect(url_for("user.admin"))

    subquery = (
        db.session.query(
            Deployment.user_id.label("user_id"), func.count().label("deployments_count")
        )
        .group_by(Deployment.user_id)
        .subquery()
    )

    # Query to join User table with the subquery
    user_deployment_counts = (
        db.session.query(
            User.username,
            User.name,
            User.email,
            User.organization,
            subquery.c.deployments_count,
        )
        .join(subquery, subquery.c.user_id == User.id)
        .all()
    )

    current_app.logger.info(user_deployment_counts[0])

    return render_template(
        "admin.html", form=form, deployment_counts=user_deployment_counts
    )


# TODO:: Remove this method entirely and change URL references
@user_bp.route("/admin/<string:username>", methods=["GET", "POST"])
@login_required
def admin_edit_user(username):
    # Redirect to the regular user edit view which enforces permissions
    # (admins are allowed to edit any user there).
    return redirect(url_for("user.edit_user", username=username))


@user_bp.route("/admin/<string:username>/delete", methods=["POST"])
@login_required
def admin_delete_user(username):
    if not current_user.admin:
        # No permission
        flash("Permission denied", "danger")
        return redirect(url_for("index.index"))

    user = User.query.filter_by(username=username).one_or_none()

    if user.id == current_user.id:
        flash("You can't delete yourself!", "danger")
        return redirect(url_for("user.admin"))

    # TODO: is this a valid SQLAlchemy method?
    user.delete()
    db.session.commit()

    flash("User deleted", "success")
    return redirect(url_for("user.admin"))
