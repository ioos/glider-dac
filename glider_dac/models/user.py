import os
import os.path
from datetime import datetime
from glider_dac import db
from flask import current_app
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from passlib.hash import sha512_crypt

class User(db.Model):
    #user_id = db.Column(db.String(255), primary_key=True)
    username = db.Column(db.String(255), primary_key=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    admin = db.Column(db.Boolean, nullable=False, default=False)
    password = db.Column(db.String(255), nullable=False)
    organization = db.Column(db.String(255))
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True))

    @classmethod
    def check_login(cls, username, password):
        user = User.query.filter_by(username=username).one_or_none()
        if user is None:
            return False
        return sha512_crypt.verify(password, user.password)

    @classmethod
    def authenticate(cls, username, password):
        if cls.check_login(username, password):
            # Return the ID of the user
            current_user = User.query.filter_by(username=username).one_or_none()
            if current_user is None:
                current_user = User(username=username)
                current_user.save()
            return current_user
        return None

    @property
    def data_root(self):
        data_root = current_app.config.get('DATA_ROOT')
        return os.path.join(data_root, self.username)

    def save(self):
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

    def get_id(self):
        return str(self.username)

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
