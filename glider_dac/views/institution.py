#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
glider_dac/views/institution.py
View definition for institutions
'''
from __future__ import unicode_literals
from flask import render_template, redirect, flash, url_for, jsonify
from flask_login import login_required, current_user
from glider_dac import app, db
from flask_wtf import Form
from wtforms import TextField, SubmitField


class NewInstitutionForm(Form):
    name = TextField('Institution Name')
    submit = SubmitField('New Institution')


@app.route('/institutions/', methods=['GET', 'POST'])
@login_required
def show_institutions():
    if not current_user.is_admin():
        flash("Permission denied", 'danger')
        return redirect(url_for('index'))
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
def get_institutions():
    institutions = [inst.to_json() for inst in db.Institution.find()]

    return jsonify(results=institutions)
