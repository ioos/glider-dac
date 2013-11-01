import os
import datetime

from flask import Flask
from flask_login import LoginManager

# Create application object
app = Flask(__name__)

app.config.from_object('glider_mission.defaults')
app.config.from_envvar('APPLICATION_SETTINGS', silent=True)

import sys

from flask.ext.mongokit import MongoKit
db = MongoKit(app)

# Mailer
from flask.ext.mail import Mail
mail = Mail(app)

# Login manager for frontend
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User Auth DB file - create if not existing
if not os.path.exists(app.config.get('USER_DB_FILE')):
    from glider_util.bdb import UserDB
    UserDB.init_db(app.config.get('USER_DB_FILE'))

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

def prettydate(d):
    if d is None:
        return "never"
    utc_dt = datetime.datetime.utcnow()
    #app.logger.info(utc_dt)
    #app.logger.info(d)
    if utc_dt > d:
        return prettypastdate(d, utc_dt - d)
    else:
        return prettyfuturedate(d, d - utc_dt)

# from http://stackoverflow.com/a/5164027/84732
def prettypastdate(d, diff):
    s = diff.seconds
    if diff.days > 7:
        return d.strftime('%d %b %y')
    elif diff.days > 1:
        return '{} days ago'.format(diff.days)
    elif diff.days == 1:
        return '1 day ago'
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '{} seconds ago'.format(s)
    elif s < 120:
        return '1 minute ago'
    elif s < 3600:
        return '{} minutes ago'.format(s/60)
    elif s < 7200:
        return '1 hour ago'
    else:
        return '{} hours ago'.format(s/3600)

def prettyfuturedate(d, diff):
    s = diff.seconds
    if diff.days > 7:
        return d.strftime('%d %b %y')
    elif diff.days > 1:
        return '{} days from now'.format(diff.days)
    elif diff.days == 1:
        return '1 day from now'
    elif s <= 1:
        return 'just now'
    elif s < 60:
        return '{} seconds from now'.format(s)
    elif s < 120:
        return '1 minute from now'
    elif s < 3600:
        return '{} minutes from now'.format(s/60)
    elif s < 7200:
        return '1 hour from now'
    else:
        return '{} hours from now'.format(s/3600)

app.jinja_env.filters['datetimeformat'] = datetimeformat
app.jinja_env.filters['timedeltaformat'] = timedeltaformat
app.jinja_env.filters['prettydate'] = prettydate

# pad/truncate filter (for making text tables)
def padfit(value, size):
    if len(value) <= size:
        return value.ljust(size)

    return value[0:(size-3)] + "..."

app.jinja_env.filters['padfit'] = padfit

def slugify(value):
    """
    Normalizes string, removes non-alpha characters, and converts spaces to hyphens.
    Pulled from Django
    """
    import unicodedata
    import re
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip())
    return unicode(re.sub('[-\s]+', '-', value))

# Import everything
import glider_mission.views
import glider_mission.models

