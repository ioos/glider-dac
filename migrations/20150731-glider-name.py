#!/usr/bin/env python

from IPython import embed
from glider_dac import app, db
from bson import ObjectId
from dateutil.parser import parse as dateparse
import sys
import re

def update():
    regex = r'(\w+)[-_](\w+)'
    for deployment in db.Deployment.find({}):
        matches = re.match(regex, deployment.name)
        glider_name = matches.group(1)
        date_str = matches.group(2)
        dateobj = dateparse(date_str, ignoretz=True)

        deployment.glider_name = glider_name
        deployment.deployment_date = dateobj
        deployment.save()



def main():
    with app.app_context():
        update()

if __name__ == '__main__':
    sys.exit(main())

