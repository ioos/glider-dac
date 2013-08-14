import os

DEBUG = False
TESTING = False
LOG_FILE = True

WEB_PASSWORD = os.environ.get("WEB_PASSWORD")
SECRET_KEY = os.environ.get("SECRET_KEY")
SERVER_NAME = os.environ.get("SERVER_NAME", None)

AUTH_HOST = os.environ.get("GLIDER_AUTH_HOST", "localhost")
AUTH_PORT = os.environ.get("GLIDER_AUTH_PORT", 22)

DATA_ROOT="/data/ftp"
