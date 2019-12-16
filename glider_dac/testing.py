import os
import urllib.parse

DEBUG = True
TESTING = True
LOG_FILE = True

DATA_ROOT="/data/ftp"

# database
MONGO_URI = os.environ.get('MONGO_URI')
url = urllib.parse.urlparse(MONGO_URI)
MONGODB_HOST = url.hostname
MONGODB_PORT = url.port
MONGODB_USERNAME = url.username
MONGODB_PASSWORD = url.password
MONGODB_DATABASE = url.path[1:]
