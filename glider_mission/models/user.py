import os
import os.path
import glob
import sys
from datetime import datetime
from glider_mission import app, db
from flask_login import UserMixin
from glider_util.bdb import UserDB
from flask.ext.mongokit import Document
from bson import ObjectId

@db.register
class User(Document):
    __collection__ = 'users'
    use_dot_notation = True
    use_schemaless = True

    structure = {
        'username'                  : unicode,
        'name'                      : unicode,
        'email'                     : unicode,
        'organization'              : unicode,
        'created'                   : datetime,
        'updated'                   : datetime
    }

    default_values = {
        'created': datetime.utcnow
    }

    @classmethod
    def _check_login(cls, username, password):
        # @TODO could be problem
        username = str(username)
        password = str(password)

        u = UserDB(app.config.get('USER_DB_FILE'))
        return u.check(username, password)

    @classmethod
    def authenticate(cls, username, password):
        if cls._check_login(username, password):
            # Return the ID of the user
            usr = db.User.find_one( { 'username' : username } )
            if usr is None:
                usr = db.User()
                usr.username = username
                usr.save()
            return usr
        return None

    @classmethod
    def update(cls, username, password):
        # @TODO could be problem
        username = str(username)
        password = str(password)

        u = UserDB(app.config.get('USER_DB_FILE'))
        return u.set(username, password)

    @property
    def data_root(self):
        data_root = app.config.get('DATA_ROOT')
        return os.path.join(data_root, self.username)

    def ensure_dir(self, dir_name):
        user_upload_dir = os.path.join(user.data_root, dir_name)
        if not os.path.exists(user_upload_dir):
            os.makedirs(user_upload_dir)

    def is_authenticated(self):
        return self.username is not None

    def is_active(self):
        return self.is_authenticated()

    def is_admin(self):
        return self.username in app.config.get("ADMINS")

    def is_anonymous(self):
        return False == self.is_active()

    def get_id(self):
        return unicode(self._id)

    @classmethod
    def get_mission_count_by_user(cls):
        return db.missions.aggregate({ '$group': { '_id': '$user_id', 'count': { '$sum' : 1 }}}).get('result',[])
