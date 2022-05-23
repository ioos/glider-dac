#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
glider_dac/models/institution.py
Model definition for Institution
'''
from datetime import datetime
from flask import current_app
from glider_dac import db
from flask_mongokit import Document


@current_app.db.register
class Institution(Document):
    __collection__ = 'institutions'
    use_dot_notation = True
    use_schemaless = True

    structure = {
        'name': str,
        'created': datetime,
        'updated': datetime
    }

    default_values = {
        'created': datetime.utcnow
    }

    indexes = [
        {
            'fields': 'name',
            'unique': True,
        },
    ]

