#!/usr/bin/env python
import os
import os.path
from datetime import datetime
import json
import shutil
import re

from flask import render_template, make_response, redirect, jsonify, flash, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
from glider_dac import app, db, datetimeformat
from glider_dac.glider_emails import send_wmoid_email
from pymongo.errors import DuplicateKeyError
from dateutil.parser import parse as dateparse
import re
from functools import wraps
from bson.objectid import ObjectId

def with_app_ctxt(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with app.app_context():
            return f(*args, **kwargs)
    return wrapper


@with_app_ctxt
def delete_deployment(deployment_id):
    deployment_id = ObjectId(deployment_id)
    deployment = db.Deployment.find_one({"_id":deployment_id})
    if deployment is not None:
        deployment.delete()

