import os
import os.path
from datetime import datetime
from glider_dac import db
from flask import current_app
from glider_util.bdb import UserDB
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class User(db.Model):
    #user_id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String, primary_key=True, nullable=False)
    name = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String)
    organization = db.Column(db.String)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True))

    indexes = [
        {
            'fields': 'username',
            'unique': True,
        },
    ]

    @classmethod
    def _check_login(cls, username, password):
        u = UserDB(current_app.config.get('USER_DB_FILE'))
        return u.check(username.encode(), password.encode())

    @classmethod
    def authenticate(cls, username, password):
        if cls._check_login(username, password):
            # Return the ID of the user
            current_user = User.query.filter_by(username=username).one()
            if current_user is None:
                current_user = User(username=username)
                current_user.save()
            return current_user
        return None

    @classmethod
    def update(cls, username, password):
        u = UserDB(current_app.config.get('USER_DB_FILE'))
        return u.set(username.encode(), password.encode())

    @property
    def data_root(self):
        data_root = current_app.config.get('DATA_ROOT')
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
        return self.username in current_app.config.get("ADMINS")

    def get_id(self):
        return str(self.username)


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
