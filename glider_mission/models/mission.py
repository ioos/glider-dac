from glider_mission import db
from datetime import datetime
from flask.ext.mongokit import Document

@db.register
class Mission(Document):
    __collection__ = 'missions'
    use_dot_notation = True
    use_schemaless = True

    structure = {
        'name'        : unicode,
        'user'        : unicode,
        'mission_dir' : unicode,
        'created'     : datetime,
        'updated'     : datetime,
    }

    default_values = {
        'created': datetime.utcnow
    }


