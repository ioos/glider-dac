from flask_login import UserMixin
import os
import os.path
import sys
from pam import authenticate
from glider_mission import app

class User(UserMixin):
    def __init__(self, id):
        self.id = id

    @classmethod
    def _check_login(cls, username, password):
        return authenticate(username, password)

    @classmethod
    def validate(cls, username, password):
        if cls._check_login(username, password):
            return User(username)

        return None

    @classmethod
    def get(cls, id):
        return User(id)

    @property
    def data_root(self):
        data_root = app.config.get('DATA_ROOT')
        return os.path.join(data_root, self.id)

    def get_missions(self):
        missions = os.listdir(self.data_root)
        retval = []

        for mission in missions:
            wmo_id_file = os.path.join(self.data_root, mission, "wmoid.txt")
            if os.path.exists(wmo_id_file):
                with open(wmo_id_file) as f:
                    retval.append((mission, f.read().strip()))
            else:
                retval.append((mission, None))

        return retval

    def new_mission(self, form):
        new_mission_dir = os.path.join(self.data_root, form.name.data)
        if not os.path.exists(new_mission_dir):
            os.mkdir(new_mission_dir)

            if form.wmo_id.data is not None and form.wmo_id.data != "":
                wmo_id_file = os.path.join(new_mission_dir, "wmoid.txt")
                with open(wmo_id_file, 'w') as f:
                    f.write(form.wmo_id.data)

