#!/usr/bin/env python
'''
scripts/update_deployments.py

A script to update (save) all the deployments in SQL DB (Deployment model)

It can be used to properly update all the old deployments latest_file and
latest_file_mtime attributes. Those attributes are updated in the .save
method of the Deployment model.

This is not a script that should be run on a schedule. Only one-offs as
necessary from within the container.
'''
from glider_dac import db
from glider_dac.models.deployemnt import Deployment
from flask import current_app

if __name__ == '__main__':
    with current_app.app_context():
        deployments = Deployment.query.all()
        for d in deployments:
            d.save()
