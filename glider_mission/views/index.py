from datetime import datetime
import os
import os.path
import sys

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from glider_mission import app, login_manager
from glider_mission.models.user import User
from flask_login import login_required, login_user, logout_user, current_user
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField

class LoginForm(Form):
    username = TextField(u'Name')
    password = PasswordField(u'Password')

class NewMissionForm(Form):
    name = TextField(u'Mission Name')
    wmo_id = TextField(u'WMO ID')

@app.route('/', methods=['GET'])
def index():
    data_root = app.config.get('DATA_ROOT')
    files = []
    missions = []
    for dirpath, dirnames, filenames in os.walk(data_root):
        rel_path = os.path.relpath(dirpath, data_root)
        path_parts = rel_path.split(os.sep)
        if len(path_parts) == 3:
            missions.append(dirpath)

        for filename in filenames:
            if filename == "wmoid.txt":
                continue

            entry = os.path.join(dirpath, filename)

            rel_path = os.path.relpath(entry, data_root)
            # user/upload/mission-name/file
            path_parts = rel_path.split(os.sep)
            if len(path_parts) != 4:
                continue

            files.append((path_parts[2], path_parts[3], datetime.fromtimestamp(os.path.getmtime(entry))))

    files = sorted(files, lambda a,b: cmp(b[2], a[2]))

    return render_template('index.html', files=files, missions=missions)

@app.route('/admin', methods=['GET'])
@login_required
def admin():
    new_mission_form = NewMissionForm()
    missions = current_user.get_missions()
    return render_template('admin.html',
                           missions=missions,
                           current_user=current_user,
                           new_mission_form=new_mission_form)

@login_manager.user_loader
def load_user(userid):
    return User.get(userid)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.validate(form.username.data, form.password.data)
        if not user:
            flash("Failed")
            return redirect(url_for("login"))

        login_user(user)
        flash("Logged in successfully")
        return redirect(request.args.get("next") or url_for("index"))

    return render_template("login.html", form=form)

@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/new_mission', methods=['POST'])
@login_required
def new_mission():
    form = NewMissionForm()
    if form.validate_on_submit():
        current_user.new_mission(form)

    return redirect(url_for('index'))

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

