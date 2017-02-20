#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
migrate.py

Perform a db migration
'''
from glider_dac import app, db
from glider_dac.models.migrations import DeploymentMigration, UserMigration
from glider_dac.models import deployment
from glider_dac.models import user

with app.app_context():
    migration = DeploymentMigration(deployment.Deployment)
    migration.migrate_all(collection=db['deployments'])
    # Go through a save all to trigger the save() method
    for m in db.Deployment.find():
        m.save()

    migration = UserMigration(user.User)
    migration.migrate_all(collection=db['users'])
