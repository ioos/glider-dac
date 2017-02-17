#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import render_template, redirect, flash, url_for, jsonify
from flask_login import login_required, current_user
from glider_dac import app, db

'''
glider_dac/views/institution.py
View definition for institutions
'''


@app.route('/institutions/', methods=['GET'])
@login_required
def show_institutions():
    if not current_user.is_admin():
        flash("Permission denied", 'danger')
        return redirect(url_for('index'))
    institutions = list(db.Institutions.find())
    return render_template('institutions.html',
                           institutions=institutions)


@app.route('/api/institution', methods=['GET'])
def get_institutions():
    institutions = [inst.to_json() for inst in db.Institution.find()]

    return jsonify(results=institutions)
