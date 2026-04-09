import os
import logging

from glider_dac.extensions import db, get_redis_connection_other

from flasgger import Swagger, LazyString, LazyJSONEncoder
from flask import Flask, request
from flask_session import Session
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_migrate import Migrate
from glider_dac.reverse_proxy import ReverseProxied
import glider_dac.signals  # noqa: F401
import os.path
import redis
from glider_dac.views.deployment import deployment_bp
from rq import Queue
from glider_dac.views.index import index_bp
from glider_dac.views.institution import institution_bp
from glider_dac.views.user import user_bp
from glider_dac.config import get_config
import glider_dac.utilities as util

from flask_security import Security, SQLAlchemyUserDatastore


log_format_str = "%(asctime)s - %(process)d - %(name)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s"
log_formatter = logging.Formatter(log_format_str)


# Create application object
def create_app():
    csrf = CSRFProtect()
    # Login manager for frontend
    login_manager = LoginManager()
    login_manager.login_view = "index.login"
    app = Flask(__name__)

    # TODO: Move elsewhere?
    app.url_map.strict_slashes = False
    app.wsgi_app = ReverseProxied(app.wsgi_app)

    csrf.init_app(app)
    app.config.update(get_config())
    # have session and remember cookie be samesite (flask/flask_login)
    app.config["REMEMBER_COOKIE_SAMESITE"] = "strict"
    app.config["SESSION_COOKIE_SAMESITE"] = "strict"
    # load REDIS prefixed environment variables
    # this is mainly for test runners which may not be using the containerized versions
    # of Redis
    # TODO: Move elsewhere, perhaps in config module?
    app.config.from_prefixed_env("OVERRIDE")
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_REDIS"] = redis.from_url(app.config["REDIS_URL"])
    app.json_encoder = LazyJSONEncoder
    template = dict(
        swaggerUiPrefix=LazyString(
            lambda: request.environ.get("HTTP_X_SCRIPT_NAME", "")
        )
    )
    Swagger(app, template=template)
    app.secret_key = app.config["SECRET_KEY"]
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_REDIS"] = redis.from_url(app.config["REDIS_URL"])
    Session(app)

    redis_connection = get_redis_connection_other(
        app.config.get("REDIS_HOST"),
        app.config.get("REDIS_PORT"),
        app.config.get("REDIS_DB"),
    )
    app.queue = Queue("default", connection=redis_connection)

    db.init_app(app)
    Migrate(app, db)
    # Ensure all models are registered with SQLAlchemy before create_all / migrations
    import glider_dac.models  # noqa: F401

    # Define models
    # Setup Flask-Security
    from glider_dac.models.user import User, Role

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    app.security = Security(app, user_datastore)
    with app.app_context():
        db.create_all()

    # Mailer
    from flask_mail import Mail

    app.mail = Mail(app)

    login_manager.init_app(app)

    from .models.user import User

    @login_manager.user_loader
    def load_user(username):
        return User.query.filter_by(username=username).one_or_none()

    app.jinja_env.filters["datetimeformat"] = util.datetimeformat
    app.jinja_env.filters["timedeltaformat"] = util.timedeltaformat
    app.jinja_env.filters["prettydate"] = util.prettydate
    app.jinja_env.filters["pluralize"] = util.pluralize
    app.jinja_env.filters["padfit"] = util.padfit

    # Create logging
    app.logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    app.logger.addHandler(stream_handler)
    if app.config.get("LOG_FILE"):
        file_handler = logging.FileHandler(
            os.path.join(os.path.dirname(__file__), "../logs/glider_dac.txt")
        )
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.info("Application Process Started")

    app.register_blueprint(index_bp)
    app.register_blueprint(deployment_bp)
    app.register_blueprint(institution_bp)
    app.register_blueprint(user_bp)

    return app
