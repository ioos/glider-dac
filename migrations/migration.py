from glider_dac import app, db
from mongokit import DocumentMigration

# Services
from glider_dac.models import deployment
class DeploymentMigration(DocumentMigration):
    def allmigration01__add_glider_name(self):
        print "Adding glider_name"
        self.target = {'glider_name':{'$exists':False}}
        self.update = {'$set':{'glider_name':u''}}

    def allmigration01__add_deployment_date(self):
        print "Adding deployment_date"
        self.target = {'deployment_date':{'$exists':False}}
        self.update = {'$set':{'deployment_date':None}}


if __name__ == '__main__':
    with app.app_context():
        migration = DeploymentMigration(deployment.Deployment)
        migration.migrate_all(collection=db['deployments'])
