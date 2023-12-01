#!/usr/bin/env python
'''
migrations/20150916_checksum.py
'''
from glider_dac import app, db
import sys

def update():
    for deployment in db.Deployment.find({'checksum':None}):
        deployment.save()

def main():
    with app.app_context():
        update()

if __name__ == '__main__':
    sys.exit(main())
