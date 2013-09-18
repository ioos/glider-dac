from glider_mission import app,db
from mongokit import DocumentMigration

# Missions
from glider_mission.models import mission
class MissionMigration(DocumentMigration):
    def allmigration01__add_deploy_fields(self):
        self.target = {'estimated_deploy_date':{'$exists': False}}
        self.update = {'$set':{'estimated_deploy_date':u'', 'estimated_deploy_location':u''}}

    def allmigration02__add_completed_field(self):
        self.target = {'completed':{'$exists': False}}
        self.update = {'$set':{'completed':False}}

# Users
from glider_mission.models import user
class UserMigration(DocumentMigration):
    # add any migrations here named "allmigration_*"
    pass

with app.app_context():
    migration = MissionMigration(mission.Mission)
    migration.migrate_all(collection=db['missions'])

    migration = UserMigration(user.User)
    migration.migrate_all(collection=db['users'])
