import os
import urllib

from glider_mission import db, slugify
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

    def on_complete(self):
        """
        sync calls here to trigger any completion tasks.

        - write or remove complete.txt
        """
        # Save a file called "completed.txt"
        completed_file = os.path.join(self.mission_dir, "completed.txt")
        if self.completed is True:
            with open(completed_file, 'w') as f:
                f.write(" ")
        else:
            if os.path.exists(completed_file):
                os.remove(completed_file)

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
