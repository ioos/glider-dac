from glider_dac import app,db
from mongokit import DocumentMigration

# Deployments
from glider_dac.models import deployment
class DeploymentMigration(DocumentMigration):
    pass

# Users
from glider_dac.models import user
class UserMigration(DocumentMigration):
    # add any migrations here named "allmigration_*"
    pass

with app.app_context():
    migration = DeploymentMigration(deployment.Deployment)
    migration.migrate_all(collection=db['deployments'])
    # Go through a save all to trigger the save() method
    for m in db.Deployment.find():
        m.save()

    migration = UserMigration(user.User)
    migration.migrate_all(collection=db['users'])
