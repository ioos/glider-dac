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
def delete_deployment(deployment_name):
    deployment = Deployment.query.filter_by(name=deployment_name).one_or_none()
    if deployment is not None:
        db.session.delete(deployment)
        db.session.commit()
