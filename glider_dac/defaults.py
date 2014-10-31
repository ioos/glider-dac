import os
import urlparse

DEBUG = False
TESTING = False
LOG_FILE = True

WEB_PASSWORD = os.environ.get("WEB_PASSWORD")
SECRET_KEY = os.environ.get("SECRET_KEY")
SERVER_NAME = os.environ.get("SERVER_NAME", None)

USER_DB_FILE = os.environ.get("USER_DB_FILE", "local-user.db")

ADMINS = os.environ.get("ADMINS", "").split(",")

DATA_ROOT = os.environ.get("DATA_ROOT")
ARCHIVE_PATH = os.environ.get("ARCHIVE_PATH")

# Hosts
PRIVATE_ERDDAP = os.environ.get('PRIVATE_ERDDAP')
PUBLIC_ERDDAP  = os.environ.get('PUBLIC_ERDDAP')
THREDDS        = os.environ.get('THREDDS')

# database
MONGO_URI = os.environ.get('MONGO_URI')
url = urlparse.urlparse(MONGO_URI)
MONGODB_HOST = url.hostname
MONGODB_PORT = url.port
MONGODB_USERNAME = url.username
MONGODB_PASSWORD = url.password
MONGODB_DATABASE = url.path[1:]

# email
MAIL_ENABLED        = os.environ.get('MAIL_ENABLED', None) == "True"
MAIL_SERVER         = os.environ.get('MAIL_SERVER')
MAIL_PORT           = os.environ.get('MAIL_PORT')
MAIL_USE_TLS        = os.environ.get("MAIL_USE_TLS", True) == "True"
MAIL_USE_SSL        = os.environ.get("MAIL_USE_SSL", False) == "True"
MAIL_USERNAME       = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD')

MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
MAIL_DEFAULT_TO     = os.environ.get('MAIL_DEFAULT_TO')
MAIL_DEFAULT_LIST   = os.environ.get('MAIL_DEFAULT_LIST', None)


