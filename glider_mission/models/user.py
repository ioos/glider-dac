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

    def get_missions(self):
        if not os.path.exists(self.data_root):
            return []

        upload_root = os.path.join(self.data_root, 'upload')
        if not os.path.exists(upload_root):
            return []

        missions = os.listdir(upload_root)
        retval = []

        for mission in missions:
            data_files = glob.glob(os.path.join(upload_root, mission, "*.nc"))
            datacount = len(data_files)

            last_updated = None
            stamps = sorted([os.stat(x).st_mtime for x in data_files])
            if len(stamps):
                last_updated = datetime.fromtimestamp(stamps[-1])

            wmo_id_file = os.path.join(upload_root, mission, "wmoid.txt")
            if os.path.exists(wmo_id_file):
                with open(wmo_id_file) as f:
                    retval.append((mission, f.read().strip(), datacount, last_updated))
            else:
                retval.append((mission, None, datacount, last_updated))

        return retval

    def new_mission(self, form):
        upload_root = os.path.join(self.data_root, 'upload')

        new_mission_dir = os.path.join(upload_root, form.name.data)
        if not os.path.exists(new_mission_dir):
            os.mkdir(new_mission_dir)

            if form.wmo_id.data is not None and form.wmo_id.data != "":
                wmo_id_file = os.path.join(new_mission_dir, "wmoid.txt")
                with open(wmo_id_file, 'w') as f:
                    f.write(form.wmo_id.data)

