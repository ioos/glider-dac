import os
import os.path
import glob
import sys
from datetime import datetime
from glider_mission import app, db
from flask_login import UserMixin
from paramiko import Transport, AuthenticationException
from flask.ext.mongokit import Document

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
        transport = Transport((app.config.get('AUTH_HOST'), app.config.get('AUTH_PORT')))
        try:
            transport.connect(username=username, password=password)
        except AuthenticationException:
            return False
        finally:
            transport.close()

        return True

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

    @property
    def data_root(self):
        data_root = app.config.get('DATA_ROOT')
        return os.path.join(data_root, self.username)

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