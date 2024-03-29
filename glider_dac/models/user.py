import os
import os.path
from datetime import datetime
from glider_dac import app, db
from glider_util.bdb import UserDB
from flask_mongokit import Document

@db.register
class User(Document):
    __collection__ = 'users'
    use_dot_notation = True
    use_schemaless = True

    structure = {
        'username'                  : str,
        'name'                      : str,
        'email'                     : str,
        'organization'              : str,
        'created'                   : datetime,
        'updated'                   : datetime
    }

    default_values = {
        'created': datetime.utcnow
    }

    indexes = [
        {
            'fields': 'username',
            'unique': True,
        },
    ]

    @classmethod
    def _check_login(cls, username, password):
        u = UserDB(app.config.get('USER_DB_FILE'))
        return u.check(username.encode(), password.encode())

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
        u = UserDB(app.config.get('USER_DB_FILE'))
        return u.set(username.encode(), password.encode())

    @property
    def data_root(self):
        data_root = app.config.get('DATA_ROOT')
        return os.path.join(data_root, self.username)

    def save(self):
        super().save()
        # on creation of user, ensure that a directory with user name is present
        self.ensure_dir("")

    def ensure_dir(self, dir_name):
        user_upload_dir = os.path.join(self.data_root, dir_name)
        if not os.path.exists(user_upload_dir):
            os.makedirs(user_upload_dir)

    def is_authenticated(self):
        return self.username is not None

    def is_active(self):
        return self.is_authenticated

    def is_anonymous(self):
        return False == self.is_active

    # This method is not provided by flask-login.  Make a property to bring it
    # in line with the rest of the expected properties from flask-login, namely:
    # is_active, is_authenticated, and is_anonymous.
    @property
    def is_admin(self):
        return self.username in app.config.get("ADMINS")

    def get_id(self):
        return str(self._id)

    @classmethod
    def get_deployment_count_by_user(cls):
        return [count for count in db.deployments.aggregate({ '$group': { '_id': '$user_id', 'count': { '$sum' : 1 }}}, cursor={})]
