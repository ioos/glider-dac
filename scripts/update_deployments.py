#!/usr/bin/env python
'''
scripts/update_deployments.py

A script update (save) all the deplyments in mongo
'''
from glider_dac import app, db

if __name__ == '__main__':
    with app.app_context():
        deployments = db.Deployment.find()
        for d in deployments:
            d.save()
