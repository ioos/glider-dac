import os
import urlparse

DEBUG = False
TESTING = False
LOG_FILE = True

WEB_PASSWORD = os.environ.get("WEB_PASSWORD")
SECRET_KEY = os.environ.get("SECRET_KEY")
SERVER_NAME = os.environ.get("SERVER_NAME", None)

AUTH_HOST = os.environ.get("GLIDER_AUTH_HOST", "localhost")
AUTH_PORT = os.environ.get("GLIDER_AUTH_PORT", 22)

ADMINS = os.environ.get("ADMINS", "").split(",")

DATA_ROOT="/data/ftp"

# database
MONGO_URI = os.environ.get('MONGO_URI')
url = urlparse.urlparse(MONGO_URI)
MONGODB_HOST = url.hostname
MONGODB_PORT = url.port
MONGODB_USERNAME = url.username
MONGODB_PASSWORD = url.password
MONGODB_DATABASE = url.path[1:]
