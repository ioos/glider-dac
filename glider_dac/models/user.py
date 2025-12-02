import os
import os.path
from datetime import datetime
from glider_dac import db
from glider_dac.utilities import email_exception_logging_wrapper
from flask import current_app
from flask_mail import Message
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from passlib.hash import sha512_crypt

class User(db.Model):
    _tablename='user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
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

    @email_exception_logging_wrapper
    def notify_user_incomplete_deployments(self):
        """
        Notify user via email of any deployments older than two weeks which have not been marked
        as completed
        """
        # Calculate the date two weeks ago
        two_weeks_ago = datetime.now() - timedelta(weeks=2)

        # Query for deployments that are not completed, last updated more than two weeks ago, and match the username
        # TODO: fix representation?
        query = (Deployment.query.filter(Deployment.completed == False,
                                         Deployment.updated < two_weeks_ago,
                                         Deployment.username == username)
                                         .order_by(Deployment.updated))
        # Convert the cursor to a list
        deployments = query.all()

        # Check if there are any deployments to notify about
        if not deployments:
            return

        # Prepare email content
        subject = f"Reminder: Incomplete Deployments for {self.name}"

        # Start building the HTML table
        body = f"""
        <html>
        <body>
            <p>User {self.name} has the following incomplete glider deployment(s) on the IOOS Glider DAC that were last updated more than two weeks ago.
               Please mark the following deployment(s) as complete if the associated deployments have finished.</p>
            <table border="1" style="border-collapse: collapse;">
                <tr>
                    <th>Deployment Name</th>
                    <th>Last Updated</th>
                </tr>
        """

        for deployment in deployments:
            body += f"""
                <tr>
                    <td>{deployment.name}</td>
                    <td>{deployment.updated.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
                """

        body += """
            </table>
        </body>
        </html>
        """

        msg = Message(subject, recipients=self.email)
        msg.html = body

        send_email_wrapper(msg)

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
