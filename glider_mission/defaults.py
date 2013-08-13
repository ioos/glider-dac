import os

DEBUG = False
TESTING = False
LOG_FILE = True

WEB_PASSWORD = os.environ.get("WEB_PASSWORD")
SECRET_KEY = os.environ.get("SECRET_KEY")
SERVER_NAME = os.environ.get("SERVER_NAME", None)

DATA_ROOT="/data/ftp"
