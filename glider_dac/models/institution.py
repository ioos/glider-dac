#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
glider_dac/models/institution.py
Model definition for Institution
'''
from datetime import datetime
from glider_dac.extensions import db


class Institution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True))
