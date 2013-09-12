import os
import os.path
from datetime import datetime

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from glider_mission import app, db

@app.route('/mission/<ObjectId:mission_id>')
def show_mission(mission_id):
    mission = db.Mission.find_one({'_id':mission_id})

    files = []
    for dirpath, dirnames, filenames in os.walk(mission.mission_dir):
        for f in filenames:
            files.append((f, datetime.fromtimestamp(os.path.getmtime(os.path.join(dirpath, f)))))

    files = sorted(files, lambda a,b: cmp(b[1], a[1]))

    return render_template('show_mission.html', mission=mission, files=files)

