#!/usr/bin/env python
'''
scripts/update_deployments.py

A script to update (save) all the deployments in mongo (Deployment model)

It can be used to properly update all the old deployments latest_file and
latest_file_mtime attributes. Those attributes are updated in the .save
method of the Deployment model.

This is not a script that should be run on a schedule. Only one-offs as
necessary from within the container.
'''
from glider_dac import app, db

if __name__ == '__main__':
    with app.app_context():
        deployments = db.Deployment.find()
        for d in deployments:
            d.save()
