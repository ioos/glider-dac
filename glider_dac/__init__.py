import os
import datetime

from glider_dac.extensions import db, get_redis_connection_other

from flasgger import Swagger, LazyString, LazyJSONEncoder
from flask import Flask, request
from flask_session import Session
from flask_cors import CORS, cross_origin
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from simplekv.memory.redisstore import RedisStore
from flask_login import LoginManager
from glider_dac.reverse_proxy import ReverseProxied
import os
import os.path
import redis
import yaml
from rq import Queue, Connection, Worker
from glider_dac.common import log_formatter
from glider_dac.views.deployment import deployment_bp
from glider_dac.views.index import index_bp
from glider_dac.views.institution import institution_bp
from glider_dac.views.user import user_bp
from glider_util import datetimeformat


csrf = CSRFProtect()
# Login manager for frontend
login_manager = LoginManager()
login_manager.login_view = "login"

#@login_manager.user_loader
#def load_user(user_id):
#    return db.User.find_one({"_id": ObjectId(user_id)})

# Create application object
def create_app():
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

    # TODO: Why does this not recognize top-level import when run in gunicorn?
    import os.path
    cur_dir = os.path.dirname(__file__)
    with open(os.path.join(cur_dir, '..', 'config.yml')) as base_config:
        config_dict = yaml.load(base_config, Loader=yaml.Loader)

    extra_config_path = os.path.join(cur_dir, '..', 'config.local.yml')
    # merge in settings from config.local.yml, if it exists
    if os.path.exists(extra_config_path):
        with open(extra_config_path) as extra_config:
            config_dict = {**config_dict, **yaml.load(extra_config,
                                                    Loader=yaml.Loader)}


    if "ENV" in app.config:
        try:
            app.config.update(config_dict[app.config["ENV"].upper()])
        except KeyError:
            app.logger.error(f"Cannot find config for {app.config['ENV']}, "
                              "falling back to DEVELOPMENT")
    else:
        app.config.update(config_dict["DEVELOPMENT"])

    app.secret_key = app.config["SECRET_KEY"]
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_REDIS"] = redis.from_url(app.config["REDIS_URL"])
    Session(app)


    redis_connection = get_redis_connection_other(app.config.get('REDIS_HOST'),
                                                  app.config.get('REDIS_PORT'),
                                                  app.config.get('REDIS_DB'))
    app.queue = Queue('default', connection=redis_connection)
    with Connection(redis_connection):
        app.worker = Worker(list(map(Queue, ["default"])))
        app.worker.work()


    import sys

    import os
    db.init_app(app)
    db.create_all()

    # Mailer
    from flask_mail import Mail
    app.mail = Mail(app)

    login_manager.init_app(app)

    app.jinja_env.filters['datetimeformat'] = util.datetimeformat
    app.jinja_env.filters['timedeltaformat'] = util.timedeltaformat
    app.jinja_env.filters['prettydate'] = util.prettydate
    app.jinja_env.filters['pluralize'] = util.pluralize
    app.jinja_env.filters['padfit'] = util.padfit

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

    app.register_blueprint(index_bp)
    app.register_blueprint(deployment_bp)
    app.register_blueprint(institution_bp)
    app.register_blueprint(user_bp)

    return app

def timedeltaformat(starting, ending):
    if isinstance(starting, datetime.datetime) and isinstance(ending, datetime.datetime):
        return ending - starting
    return "unknown"

def prettydate(d):
    if d is None:
        return "never"
    utc_dt = datetime.datetime.utcnow()
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

# TODO: move to CSS `text-overflow: ellipsis;`
# pad/truncate filter (for making text tables)
def padfit(value, size):
    if len(value) <= size:
        return value.ljust(size)

    return value[0:(size-3)] + "..."


def slugify(value):
    """
    Normalizes string, removes non-alpha characters, and converts spaces to hyphens.
    Pulled from Django
    """
    value = re.sub(r'[^\w\s-]', '', value).strip()
    return re.sub(r'[-\s]+', '-', value)

# Import everything
import glider_dac.views
import glider_dac.models
