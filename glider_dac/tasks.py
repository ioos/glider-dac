#!/usr/bin/env python
import os
import os.path
from datetime import datetime
import json
import shutil
import re

from flask import (render_template, make_response, redirect, jsonify, flash, url_for, request,
                   current_app)
from flask_login import login_required, login_user, logout_user, current_user
from glider_dac import db
from glider_util import datetimeformat
from pymongo.errors import DuplicateKeyError
from dateutil.parser import parse as dateparse
import re
from functools import wraps

def with_app_ctxt(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with current_app.app_context():
            return f(*args, **kwargs)
    return wrapper


@with_app_ctxt
def delete_deployment(deployment_id):
    deployment_id = ObjectId(deployment_id)
    deployment = db.Deployment.find_one({"_id":deployment_id})
    if deployment is not None:
        deployment.delete()
