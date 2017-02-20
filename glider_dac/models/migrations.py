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

