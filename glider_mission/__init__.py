import os
import datetime

from flask import Flask
from flask_login import LoginManager

# Create application object
app = Flask(__name__)

app.config.from_object('glider_mission.defaults')
app.config.from_envvar('APPLICATION_SETTINGS', silent=True)

import sys

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Create logging
if app.config.get('LOG_FILE') == True:
    import logging
    from logging import FileHandler
    file_handler = FileHandler('logs/glider_mission.txt')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

# Create datetime jinja2 filter
def datetimeformat(value, format='%a, %b %d %Y at %I:%M%p'):
    if isinstance(value, datetime.datetime):
        return value.strftime(format)
    return value

def timedeltaformat(starting, ending):
    if isinstance(starting, datetime.datetime) and isinstance(ending, datetime.datetime):
        return ending - starting
    return "unknown"

app.jinja_env.filters['datetimeformat'] = datetimeformat
app.jinja_env.filters['timedeltaformat'] = timedeltaformat

# pad/truncate filter (for making text tables)
def padfit(value, size):
    if len(value) <= size:
        return value.ljust(size)

    return value[0:(size-3)] + "..."

app.jinja_env.filters['padfit'] = padfit

# Import everything
import glider_mission.views
import glider_mission.models

