import os
import urllib
import hashlib
import subprocess
import warnings

from glider_mission import app, db, slugify
from datetime import datetime
from flask.ext.mongokit import Document
from bson.objectid import ObjectId

@db.register
class Mission(Document):
    __collection__   = 'missions'
    use_dot_notation = True
    use_schemaless   = True

    structure = {
        'name'                      : unicode,
        'user_id'                   : ObjectId,
        'username'                  : unicode,  # The cached username to lightly DB load
        'operator'                  : unicode,  # The operator of this Glider. Shows up in TDS as the title.
        'mission_dir'               : unicode,
        'estimated_deploy_date'     : datetime,
        'estimated_deploy_location' : unicode,  # WKT text
        'wmo_id'                    : unicode,
        'completed'                 : bool,
        'created'                   : datetime,
        'updated'                   : datetime
    }

    default_values = {
        'created': datetime.utcnow,
        'completed': False
    }

    def save(self):
        if self.username is None or self.username == u'':
            user = db.User.find_one( { '_id' : self.user_id } )
            self.username = user.username

        self.updated = datetime.utcnow()

        self.sync()
        super(Mission, self).save()

    @property
    def dap(self):
        return u"http://tds.gliders.ioos.us/thredds/dodsC/%s_%s_Time.ncml" % (slugify(self.title), slugify(self.name))

    @property
    def sos(self):
        return u"http://tds.gliders.ioos.us/thredds/sos/%s_%s_Time.ncml" % (slugify(self.title), slugify(self.name))

    @property
    def iso(self):
        title = slugify(self.title)
        name = slugify(self.name)
        catalog_parameter = u'http://tds.gliders.ioos.us/thredds/%s/%s/catalog.html' % (title, name)
        dataset_parameter = u'%s_%s_Time' % (title, name)
        query = urllib.urlencode({ 'catalog' : catalog_parameter, 'dataset' : dataset_parameter })
        return u"http://tds.gliders.ioos.us/thredds/iso/%s_%s_Time.ncml?%s" % (title, name, query)

    @property
    def title(self):
        if self.operator is not None and self.operator != "":
            return self.operator
        else:
            return self.username

    def _hash_file(self, fname):
        """
        Calculates an md5sum of the passed in file (absolute path).

        Based on http://stackoverflow.com/a/4213255/84732
        """
        md5 = hashlib.md5()

        with open(fname, 'rb') as f:
            for chunk in iter(lambda: f.read(128), b''):
                md5.update(chunk)

        return md5.hexdigest()

    def on_complete(self):
        """
        sync calls here to trigger any completion tasks.

        - write or remove complete.txt
        - generate/update md5 files (removed on not-complete)
        """
        # Save a file called "completed.txt"
        completed_file = os.path.join(self.mission_dir, "completed.txt")
        if self.completed is True:
            with open(completed_file, 'w') as f:
                f.write(" ")
        else:
            if os.path.exists(completed_file):
                os.remove(completed_file)

        # generate md5s of all data files on completion
        if self.completed:
            for dirpath, dirnames, filenames in os.walk(self.mission_dir):
                for f in filenames:
                    if f in ["mission.json", "wmoid.txt", "completed.txt"] or f.endswith(".md5"):
                        continue

                    full_file = os.path.join(dirpath, f)
                    md5_file = full_file + ".md5"

                    # only calc md5 if it does not exist, this is expensive!
                    if os.path.exists(md5_file):
                        continue

                    md5_value = self._hash_file(full_file)

                    md5_file = full_file + ".md5"
                    with open(md5_file, 'w') as mf:
                        mf.write(md5_value)
        else:
            for dirpath, dirnames, filenames in os.walk(self.mission_dir):
                for f in filenames:
                    if f.endswith(".md5"):
                        os.unlink(os.path.join(dirpath, f))

        # link to archive user's ftp dir
        # this will only work on production
        if self.completed:
            try:
                archive_path = app.config.get('ARCHIVE_PATH')

                _, mname = os.path.split(self.mission_dir)
                archive_mdir = os.path.join(archive_path, mname)
                if not os.path.exists(archive_mdir):
                    os.makedirs(archive_mdir)

                # local test
                #os.symlink(self.mission_dir, archive_mdir)

                subprocess.call(['/usr/local/bin/bindfs', '--perms=a-w', self.mission_dir, archive_mdir])

            except Exception as e:
                warnings.warn("Could not link %s to %s: %s" % (self.mission_dir, archive_mdir, e))

    def sync(self):
        if not os.path.exists(self.mission_dir):
            try:
                os.makedirs(self.mission_dir)
            except OSError:
                pass

        # Keep the WMO file updated if it is edited via the web form
        if self.wmo_id is not None and self.wmo_id != "":
            wmo_id_file = os.path.join(self.mission_dir, "wmoid.txt")
            with open(wmo_id_file, 'w') as f:
                f.write(self.wmo_id)

        # trigger any completed tasks if necessary
        self.on_complete()

        # Serialize Mission model to disk
        json_file = os.path.join(self.mission_dir, "mission.json")
        with open(json_file, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def get_mission_count_by_operator(cls):
        return db.missions.aggregate({ '$group': { '_id': '$operator', 'count': { '$sum' : 1 }}}).get('result',[])
