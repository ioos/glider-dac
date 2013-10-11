from datetime import datetime
import os
import os.path
import sys

import pymongo
from bson.objectid import ObjectId

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from glider_mission import app, login_manager, db
from glider_mission.models.user import User
from flask_login import login_required, login_user, logout_user, current_user
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField

class LoginForm(Form):
    username = TextField(u'Name')
    password = PasswordField(u'Password')

@app.route('/', methods=['GET'])
def index():

    data_root = app.config.get('DATA_ROOT')

    files = []
    missions_by_dir = {}
    for dirpath, dirnames, filenames in os.walk(data_root):
        rel_path = os.path.relpath(dirpath, data_root)
        path_parts = rel_path.split(os.sep)

        for filename in filenames:
            if filename == "wmoid.txt":
                continue

            entry = os.path.join(dirpath, filename)

            if dirpath not in missions_by_dir:
                missions_by_dir[dirpath] = db.Mission.find_one({'mission_dir':dirpath})

            rel_path = os.path.relpath(entry, data_root)

            # user/upload/mission-name/file
            path_parts = rel_path.split(os.sep)
            if len(path_parts) != 4:
                continue

            files.append((path_parts[0], path_parts[2], path_parts[3], datetime.fromtimestamp(os.path.getmtime(entry)), missions_by_dir[dirpath]))

    files = sorted(files, lambda a,b: cmp(b[3], a[3]))

    missions = list(db.Mission.find(sort=[("updated" , pymongo.DESCENDING)], limit=20))

    for m in missions:
        f = filter(lambda x: x[4] == m, files)
        if len(f):
            m.updated = f[0][3]

    missions = sorted(missions, lambda a,b: cmp(b.updated, a.updated))

    user_missions = User.get_mission_count_by_user()
    user_map = {u._id:u for u in db.User.find()}

    return render_template('index.html', files=files, missions=missions, user_missions=user_missions, user_map=user_map)

@login_manager.user_loader
def load_user(userid):
    return db.User.find_one({ "_id" : ObjectId(userid) })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_active():
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

    return render_template("login.html", form=form)

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

