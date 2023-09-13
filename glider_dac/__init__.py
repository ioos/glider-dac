import os
import datetime

from flasgger import Swagger, LazyString, LazyJSONEncoder
from flask import Flask, request
from flask_kvsession import KVSessionExtension
from flask_cors import CORS, cross_origin
from flask_wtf import CSRFProtect
from simplekv.memory.redisstore import RedisStore
from flask_login import LoginManager
from glider_dac.reverse_proxy import ReverseProxied
import redis
import yaml
from glider_dac.common import log_formatter


csrf = CSRFProtect()

# Create application object
app = Flask(__name__)
app.url_map.strict_slashes = False
app.wsgi_app = ReverseProxied(app.wsgi_app)

csrf.init_app(app)
app.config['SWAGGER'] = {
    'title': 'glider-dac',
    'uiversion': 3,
    'openapi': '3.0.2'
}
app.json_encoder = LazyJSONEncoder
template = dict(swaggerUiPrefix=LazyString(lambda : request.environ.get('HTTP_X_SCRIPT_NAME', '')))
Swagger(app, template=template)

cur_dir = os.path.dirname(__file__)
with open(os.path.join(cur_dir, '..', 'config.yml')) as base_config:
    config_dict = yaml.load(base_config, Loader=yaml.Loader)

extra_config_path = os.path.join(cur_dir, '..', 'config.local.yml')
# merge in settings from config.local.yml, if it exists
if os.path.exists(extra_config_path):
    with open(extra_config_path) as extra_config:
        config_dict = {**config_dict, **yaml.load(extra_config,
                                                  Loader=yaml.Loader)}

try:
    app.config.update(config_dict["PRODUCTION"])
except KeyError:
    app.config.update(config_dict["DEVELOPMENT"])

import redis
redis_pool = redis.ConnectionPool(host=app.config.get('REDIS_HOST'),
                                  port=app.config.get('REDIS_PORT'),
                                  db=app.config.get('REDIS_DB'))
redis_connection = redis.Redis(connection_pool=redis_pool)
strict_redis = redis.StrictRedis(connection_pool=redis_pool)

store = RedisStore(strict_redis)

KVSessionExtension(store, app)

from rq import Queue
queue = Queue('default', connection=redis_connection)

import sys

from flask_mongokit import MongoKit
import os
db = MongoKit(app)

# Mailer
from flask_mail import Mail
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
    file_handler = FileHandler(os.path.join(os.path.dirname(__file__),
                                            '../logs/glider_dac.txt'))
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('Application Process Started')

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
        return d.strftime('%Y %b %d')
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
        return '{} minutes ago'.format(s//60)
    elif s < 7200:
        return '1 hour ago'
    else:
        return '{} hours ago'.format(s//3600)

def prettyfuturedate(d, diff):
    s = diff.seconds
    if diff.days > 7:
        return d.strftime('%Y %b %d')
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

def pluralize(number, singular = '', plural = 's'):
    if number == 1:
        return singular
    else:
        return plural

# pad/truncate filter (for making text tables)
def padfit(value, size):
    if len(value) <= size:
        return value.ljust(size)

    return value[0:(size-3)] + "..."

app.jinja_env.filters['datetimeformat'] = datetimeformat
app.jinja_env.filters['timedeltaformat'] = timedeltaformat
app.jinja_env.filters['prettydate'] = prettydate
app.jinja_env.filters['pluralize'] = pluralize
app.jinja_env.filters['padfit'] = padfit

def slugify(value):
    """
    Normalizes string, removes non-alpha characters, and converts spaces to hyphens.
    Pulled from Django
    """
    import unicodedata
    import re
    #value = str(value)
    #value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub(r'[^\w\s-]', '', value).strip()
    return re.sub(r'[-\s]+', '-', value)

# Import everything
import glider_dac.views
import glider_dac.models

