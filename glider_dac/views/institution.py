#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
glider_dac/views/institution.py
View definition for institutions
'''

from flask import render_template, redirect, flash, url_for, jsonify, request
from flask_cors import cross_origin
from flask_login import current_user
from glider_dac import app, db
from flask_wtf import Form
from wtforms import TextField, SubmitField
from functools import wraps
import json


def error_wrapper(func):
    '''
    Function wrapper to catch exceptions and return them as jsonified errors
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return jsonify(error=type(e).__name__, message=e.message), 500
    return wrapper


def admin_required(func):
    '''
    Wraps a route to require an administrator
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        if app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return app.login_manager.unauthorized()
        elif not current_user.is_admin:
            flash("Permission denied", 'danger')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return wrapper


class NewInstitutionForm(Form):
    name = TextField('Institution Name')
    submit = SubmitField('New Institution')


@app.route('/institutions/', methods=['GET', 'POST'])
@admin_required
def show_institutions():
    institutions = list(db.Institution.find())
    form = NewInstitutionForm()
    if form.validate_on_submit():
        institution = db.Institution()
        institution.name = form.name.data
        institution.save()
        flash('Institution Created', 'success')

    return render_template('institutions.html',
                           form=form,
                           institutions=institutions)


@app.route('/api/institution', methods=['GET'])
@cross_origin()
def get_institutions():
    institutions = [json.loads(inst.to_json()) for inst in db.Institution.find()]
    return jsonify(results=institutions)


@app.route('/api/institution', methods=['POST'])
@admin_required
@error_wrapper
def new_institution():
    app.logger.info(request.data)
    data = json.loads(request.data)
    institution = db.Institution()
    institution.name = data['name']
    institution.save()
    return institution.to_json()


@app.route('/api/institution/<ObjectId:institution_id>', methods=['DELETE'])
@admin_required
@error_wrapper
def delete_institution(institution_id):
    if not current_user.is_admin:
        flash("Permission denied", 'danger')
        return redirect(url_for('index'))
    institution = db.Institution.find_one({"_id": institution_id})
    if institution is None:
        return jsonify({}), 404
    app.logger.info("Deleting institution")
    institution.delete()
    return jsonify({}), 204

