#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
glider_dac/models/deployment.py
Model definition for a Deployment
'''
from flask import current_app
from glider_dac import slugify
from glider_dac.extensions import db
from geoalchemy2.types import Geometry
#from sqlalchemy import event
from flask_sqlalchemy import models_committed
#from glider_dac.worker import queue
from glider_dac.glider_emails import glider_deployment_check
from datetime import datetime
#from flask_mongokit import Document
from bson.objectid import ObjectId
from rq import Queue, Connection, Worker
from shutil import rmtree
import os
import glob
import hashlib



class Deployment(db.Model):
    deployment_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"))
    #'username': str,  # The cached username to lightly DB load
    # The operator of this Glider. Shows up in TDS as the title.
    operator = db.Column(db.String, nullable=False)
    deployment_dir = db.Column(db.String, unique=True, nullable=False)
    #estimated_deploy_date: datetime,
    estimated_deploy_location = db.Column(Geometry(geometry_type='POINT',
                                                   srid=4326))
    # TODO: Add constraints for WMO IDs??
    wmo_id = db.Column(db.String)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created = db.Column(db.DateTime(timezone=True), nullable=False,
                        default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), nullable=False)
    glider_name = db.Column(db.String, nullable=False)
    deployment_date = db.Column(db.DateTime(timezone=True), nullable=False)
    archive_safe = db.Column(db.Boolean, nullable=False, default=True)
    checksum = db.Column(db.String)
    attribution = db.Column(db.String)
    delayed_mode = db.Column(db.Boolean, nullable=False, default=False)
    latest_file = db.Column(db.String)
    latest_file_mtime = db.Column(db.DateTime(timezone=True))
    compliance_check_passed = db.Column(db.Boolean, nullable=False,
                                        default=False)
    compliance_check_report = db.Column(db.JSON)


    def save(self):
        if self.username is None or self.username == '':
            user = db.User.find_one({'_id': self.user_id})
            self.username = user.username


        # Update the stats on the latest profile file
        modtime = None
        latest_file = self.get_latest_nc_file()
        if latest_file:  # if there are indeed files, get name and modtime
            modtime = datetime.fromtimestamp(os.path.getmtime(latest_file))
            latest_file = os.path.basename(latest_file)
        self.latest_file = latest_file
        self.latest_file_mtime = modtime

        self.sync()
        self.updated = datetime.utcnow()
        app.logger.info("Update time is %s", self.updated)
        update_vals = dict(self)
        try:
            doc_id = update_vals.pop("_id")
        # if we get a KeyError, this is a new deployment that hasn't been entered into the database yet
        # so we need to save it.  This is when you add "New deployment" while logged in -- files must
        # later be added
        except KeyError:
            Document.save(self)
        # otherwise, need to use update/upsert via Pymongo in case of queued job for
        # compliance so that result does not get clobbered.
        # use $set instead of replacing document
        else:
            db.deployments.update({"_id": doc_id}, {"$set": update_vals}, upsert=True)
        # HACK: special logic for Navy gliders deployment
        if self.username == "navoceano" and self.glider_name.startswith("ng"):
            glob_path = os.path.join(app.config.get('DATA_ROOT'),
                                     "hurricanes-20230601T000",
                                     f"{self.glider_name}*")
            for deployment_file in glob.iglob(glob_path):
                symlink_dest = os.path.join('deployment_dir',
                                            deployment_file.name.replace("_", "-"))
                try:
                    os.symlink(deployment_file, symlink_dest)
                except OSError:
                    logger.exception(f"Could not symlink {symlink_dest}")

    def delete(self):
        if os.path.exists(self.full_path):
            rmtree(self.full_path)
        if os.path.exists(self.public_erddap_path):
            rmtree(self.public_erddap_path)
        if os.path.exists(self.thredds_path):
            rmtree(self.thredds_path)
    @property
    def dap(self):
        '''
        Returns the THREDDS DAP URL to this deployment
        '''
        args = {
            'host': current_app.config['THREDDS'],
            'user': slugify(self.username),
            'deployment': slugify(self.name)
        }
        dap_url = "http://%(host)s/thredds/dodsC/deployments/%(user)s/%(deployment)s/%(deployment)s.nc3.nc" % args
        return dap_url

    @property
    def sos(self):
        '''
        Returns the URL to the NcSOS endpoint
        '''
        args = {
            'host': current_app.config['THREDDS'],
            'user': slugify(self.username),
            'deployment': slugify(self.name)
        }
        sos_url = "http://%(host)s/thredds/sos/deployments/%(user)s/%(deployment)s/%(deployment)s.nc3.nc?service=SOS&request=GetCapabilities&AcceptVersions=1.0.0" % args
        return sos_url

    @property
    def iso(self):
        name = slugify(self.name)
        iso_url = 'http://%(host)s/erddap/tabledap/%(name)s.iso19115' % {
            'host': current_app.config['PUBLIC_ERDDAP'], 'name': name}
        return iso_url

    @property
    def thredds(self):
        args = {
            'host': current_app.config['THREDDS'],
            'user': slugify(self.username),
            'deployment': slugify(self.name)
        }
        thredds_url = "http://%(host)s/thredds/catalog/deployments/%(user)s/%(deployment)s/catalog.html?dataset=deployments/%(user)s/%(deployment)s/%(deployment)s.nc3.nc" % args
        return thredds_url

    @property
    def erddap(self):
        args = {
            'host': current_app.config['PUBLIC_ERDDAP'],
            'user': slugify(self.username),
            'deployment': slugify(self.name)
        }
        erddap_url = "http://%(host)s/erddap/tabledap/%(deployment)s.html" % args
        return erddap_url

    @property
    def title(self):
        if self.operator is not None and self.operator != "":
            return self.operator
        else:
            return self.username

    @property
    def full_path(self):
        return os.path.join(current_app.config.get('DATA_ROOT'), self.deployment_dir)

    @property
    def public_erddap_path(self):
        return os.path.join(current_app.config.get('PUBLIC_DATA_ROOT'), self.deployment_dir)

    @property
    def thredds_path(self):
        return os.path.join(current_app.config.get('THREDDS_DATA_ROOT'), self.deployment_dir)

    def on_complete(self):
        """
        sync calls here to trigger any completion tasks.

        - write or remove complete.txt
        - generate/update md5 files (removed on not-complete)
        - link/unlink via bindfs to archive dir
        - schedule checker report against ERDDAP endpoint
        """
        # Save a file called "completed.txt"
        completed_file = os.path.join(self.full_path, "completed.txt")
        if self.completed is True:
            with open(completed_file, 'w') as f:
                f.write(" ")
        else:
            if os.path.exists(completed_file):
                os.remove(completed_file)

        # generate md5s of all data files on completion
        if self.completed:
            for dirpath, dirnames, filenames in os.walk(self.full_path):
                for f in filenames:
                    if (f in ["deployment.json", "wmoid.txt", "completed.txt"]
                        or f.endswith(".md5") or not f.endswith('.nc')):
                        continue

                    full_file = os.path.join(dirpath, f)
            # schedule the checker job to kick off the compliance checker email
            # on the deployment when the deployment is completed
            # on_complete might be a misleading function name -- this section
            # can run any time there is a sync, so check if a checker run has already been executed
            # if compliance check failed or has not yet been run, go ahead to next section
            if not getattr(self, "compliance_check_passed", None):
                app.logger.info("Scheduling compliance check for completed "
                                "deployment {}".format(self.deployment_dir))
                queue.enqueue(glider_deployment_check,
                              kwargs={"deployment_dir": self.deployment_dir},
                              job_timeout=800)
        else:
            for dirpath, dirnames, filenames in os.walk(self.full_path):
                for f in filenames:
                    if f.endswith(".md5"):
                        os.unlink(os.path.join(dirpath, f))

    def get_latest_nc_file(self):
        '''
        Returns the latest netCDF file found in the directory

        :param str root: Root of the directory to scan
        '''
        list_of_files = glob.glob('{}/*.nc'.format(self.full_path))
        if not list_of_files:  # Check for no files
            return None
        return max(list_of_files, key=os.path.getmtime)

    def calculate_checksum(self):
        '''
        Calculates a checksum for the deployment based on the MongoKit to_json()
        serialization and the modified time(s) of the dive file(s).
        '''
        md5 = hashlib.md5()
        # Now add the modified times for the dive files in the deployment directory
        # We dont MD5 every dive file here to save time
        for dirpath, dirnames, filenames in os.walk(self.full_path):
            for f in filenames:
                # could simply do `not f.endswith(.nc)`
                if (f in ["deployment.json", "wmoid.txt", "completed.txt"]
                    or f.endswith(".md5") or not f.endswith('.nc')):
                    continue
                mtime = os.path.getmtime(os.path.join(dirpath, f))
                mtime = datetime.utcfromtimestamp(mtime)

                md5.update(mtime.isoformat().encode('utf-8'))
        self.checksum = md5.hexdigest()

    def sync(self):
        if current_app.config.get('NODATA'):
            return
        if not os.path.exists(self.full_path):
            try:
                os.makedirs(self.full_path)
            except OSError:
                pass

        # trigger any completed tasks if necessary
        self.update_wmoid_file()
        self.on_complete()
        self.calculate_checksum()

        # Serialize Deployment model to disk
        json_file = os.path.join(self.full_path, "deployment.json")
        with open(json_file, 'w') as f:
            f.write(self.to_json())

    def update_wmoid_file(self):
        # Keep the WMO file updated if it is edited via the web form
        wmo_id = ""
        if self.wmo_id is not None and self.wmo_id != "":
            wmo_id_file = os.path.join(self.full_path, "wmoid.txt")
            if os.path.exists(wmo_id_file):
                # Read the wmo_id from file
                with open(wmo_id_file, 'r') as f:
                    wmo_id = str(f.readline().strip())

            if wmo_id != self.wmo_id:
                # Write the new wmo_id to file if new
                with open(wmo_id_file, 'w') as f:
                    f.write(self.wmo_id)
    @classmethod
    def get_deployment_count_by_operator(cls):
        return [count for count in db.deployments.aggregate({'$group': {'_id':
                                                                        '$operator',
                                                                        'count':
                                                                        {'$sum':
                                                                         1}}},
                                                            cursor={})]

def on_models_committed(sender, changes):
    for model, operation in changes:
        if isinstance(model, Deployment):
            if operation == "insert" or operation == "update":
                model.save()
            elif operation == "delete":
                model.delete()
