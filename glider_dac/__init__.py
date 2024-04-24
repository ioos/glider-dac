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
from glider_dac.models.user import User
from sqlalchemy import event
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
import glider_dac.utilities as util


csrf = CSRFProtect()
# Login manager for frontend
login_manager = LoginManager()
login_manager.login_view = "index.login"

# Create application object
def create_app():
    app = Flask(__name__)

    # TODO: Move elsewhere?
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
    #with Connection(redis_connection):
    #    app.worker = Worker(list(map(Queue, ["default"])))
    #    app.worker.work()


    import sys

    import os

    db.init_app(app)

    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def load_spatialite(dbapi_conn, connection_record):
            if str(db.engine.url).startswith("sqlite:"):
                # From # https://geoalchemy-2.readthedocs.io/en/latest/spatialite_tutorial.html
                dbapi_conn.enable_load_extension(True)
                # HACK: hardcoded for Docker -- find another means of loading
                # on other possible OSes
                dbapi_conn.load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite.so')

        db.create_all()

    # Mailer
    from flask_mail import Mail
    app.mail = Mail(app)

    login_manager.init_app(app)

    from .models.user import User
    @login_manager.user_loader
    def load_user(username):
        return User.query.filter_by(username=username).one_or_none()

    app.jinja_env.filters['datetimeformat'] = util.datetimeformat
    app.jinja_env.filters['timedeltaformat'] = util.timedeltaformat
    app.jinja_env.filters['prettydate'] = util.prettydate
    app.jinja_env.filters['pluralize'] = util.pluralize
    app.jinja_env.filters['padfit'] = util.padfit

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

# Import everything
import glider_dac.views
import glider_dac.models
