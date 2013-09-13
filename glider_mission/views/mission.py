import os
import os.path
from datetime import datetime

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
from glider_mission import app, db

from flask.ext.wtf import Form
from wtforms import TextField, SubmitField

class MissionForm(Form):
    estimated_deploy_date       = TextField(u'Estimated Deploy Date (yyyy-mm-dd)')
    estimated_deploy_location   = TextField(u'Estimated Deploy Location (WKT)')
    wmo_id                      = TextField(u'WMO ID')
    submit                      = SubmitField(u'Submit')

class NewMissionForm(Form):
    name    = TextField(u'Mission Name')
    wmo_id  = TextField(u'WMO ID')
    submit  = SubmitField(u"Create")

@app.route('/users/<string:username>/missions')
def list_user_missions(username):
    user = db.User.find_one( {'username' : username } )
    missions = db.Mission.find( { 'user_id' : user._id } )

    if current_user and current_user.is_active() and (current_user.is_admin() or current_user == user):
        # Permission to edit
        form = NewMissionForm()
        return render_template('edit_user_missions.html', username=username, form=form, missions=missions)
    else:  # No permission to edit
        return render_template('list_user_missions.html', username=username, missions=missions)

    
@app.route('/users/<string:username>/mission/<ObjectId:mission_id>')
def show_mission(username, mission_id):
    user = db.User.find_one( {'username' : username } )
    mission = db.Mission.find_one({'_id':mission_id})

    files = []
    for dirpath, dirnames, filenames in os.walk(mission.mission_dir):
        for f in filenames:
            files.append((f, datetime.fromtimestamp(os.path.getmtime(os.path.join(dirpath, f)))))

    files = sorted(files, lambda a,b: cmp(b[1], a[1]))

    if current_user and current_user.is_active() and (current_user.is_admin() or current_user == user):
        # Permissions to edit
        form = MissionForm(obj=mission)
        return render_template('edit_mission.html', username=username, form=form, mission=mission, files=files)
    else:  # No permissions to edit
        return render_template('show_mission.html', username=username, mission=mission, files=files)

@app.route('/mission/<ObjectId:mission_id>')
def show_mission_no_username(mission_id):
    mission = db.Mission.find_one( { '_id' : mission_id } )
    username = db.User.find_one( { '_id' : mission.user_id } ).username
    return redirect(url_for('show_mission', username=username, mission_id=mission._id))
    
@app.route('/users/<string:username>/mission/new', methods=['POST'])
@login_required
def new_mission(username):
    user = db.User.find_one( {'username' : username } )
    if user is None or (user is not None and not current_user.is_admin() and current_user != user):
        # No permission
        flash("Permission denied")
        return redirect(url_for("index"))

    form = NewMissionForm()

    if form.validate_on_submit():

        upload_root = os.path.join(user.data_root, 'upload')
        new_mission_dir = os.path.join(upload_root, form.name.data)

        mission = db.Mission()
        form.populate_obj(mission)
        mission.user_id = user._id
        mission.mission_dir = new_mission_dir
        mission.updated = datetime.utcnow()
        mission.save()
        mission.sync()
        flash("Mission created")

    return redirect(url_for('list_user_missions', username=username))


@app.route('/users/<string:username>/mission/<ObjectId:mission_id>/edit', methods=['POST'])
@login_required
def edit_mission(username, mission_id):

    user = db.User.find_one( {'username' : username } )
    if user is None or (user is not None and not current_user.is_admin() and current_user != user):
        # No permission
        flash("Permission denied")
        return redirect(url_for('list_user_missions', username=username))

    mission = db.Mission.find_one({'_id':mission_id})

    form = MissionForm(obj=mission)

    if form.validate_on_submit():
        form.populate_obj(mission)
        mission.updated = datetime.utcnow()
        try:
            mission.estimated_deploy_date = datetime.strptime(form.estimated_deploy_date.data, "%Y-%m-%d")
        except ValueError:
            mission.estimated_deploy_date = None
        mission.save()
        mission.sync()
        flash("Mission updated")
        return redirect(url_for('show_mission', username=username, mission_id=mission._id))

    return render_template('edit_mission.html', username=username, form=form, mission=mission)
