#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
glider_dac/models/deployment.py
Model definition for a Deployment
'''
from flask import current_app, render_template
from flask_mail import Message
from glider_dac.utilities import (slugify, slugify_sql,
                                  email_exception_logging_wrapper,
                                  get_thredds_catalog_url,
                                  get_erddap_catalog_url)
from glider_dac.extensions import db
from glider_dac.models.user import User
#from geoalchemy2.types import Geometry
import geojson
from compliance_checker.suite import CheckSuite
from flask_sqlalchemy.track_modifications import models_committed
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, relationship
from marshmallow.fields import Field, Method
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.convert import ModelConverter
from datetime import datetime
from rq import Queue, Connection, Worker
from shutil import rmtree
import os
import glob
import hashlib



class Deployment(db.Model):
    name = db.Column(db.String(255), unique=True, nullable=False, index=True,
                     primary_key=True)
    username = db.Column(db.String(255), db.ForeignKey("user.username"))
    user = db.relationship("User", lazy='joined', backref="deployment")
    # The operator of this Glider. Shows up in TDS as the title.
    operator = db.Column(db.String(255), nullable=True)#nullable=False)
    deployment_dir = db.Column(db.String(255), nullable=False)
    #estimated_deploy_location = db.Column(Geometry(geometry_type='POINT',
    #                                               srid=4326))
    # TODO: Add constraints for WMO IDs??
    wmo_id = db.Column(db.String(255))
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created = db.Column(db.DateTime(timezone=True), nullable=False,
                        default=datetime.utcnow)
    updated = db.Column(db.DateTime(timezone=True), nullable=False)
    glider_name = db.Column(db.String(255), nullable=False)
    deployment_date = db.Column(db.DateTime(timezone=True), nullable=True) # nullable=
    archive_safe = db.Column(db.Boolean, nullable=False, default=True)
    checksum = db.Column(db.String(255))
    attribution = db.Column(db.Text)
    delayed_mode = db.Column(db.Boolean, nullable=True, default=False)
    latest_file = db.Column(db.String(255))
    latest_file_mtime = db.Column(db.DateTime(timezone=True))
    compliance_check_passed = db.Column(db.Boolean, nullable=False,
                                        default=False)
    compliance_check_report = db.Column(db.JSON, nullable=True)
    cf_standard_names_valid = db.Column(db.Boolean, nullable=True)


    def save(self):
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
        try:
            doc_id = update_vals.pop("_id")
        # if we get a KeyError, this is a new deployment that hasn't been entered into the database yet
        # so we need to save it.  This is when you add "New deployment" while logged in -- files must
        # later be added
        except KeyError:
            # TODO: Update for SQLAlchemy
            pass
        # otherwise, need to use update/upsert via Pymongo in case of queued job for
        # compliance so that result does not get clobbered.
        # use $set instead of replacing document
        else:
            db.session.commit()
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

    def delete_deployment(self):
        self.delete_files()
        db.session.delete(self)
        db.session.commit()

    def delete_files(self):
        if os.path.exists(self.full_path):
            rmtree(self.full_path)
        if os.path.exists(self.public_erddap_path):
            rmtree(self.public_erddap_path)
        if os.path.exists(self.thredds_path):
            rmtree(self.thredds_path)

    @hybrid_property
    def dap(self):
        '''
        Returns the THREDDS DAP URL to this deployment
        '''
        host = current_app.config['THREDDS']
        user = self.username
        deployment = self.name
        dap_url = "http://" + host + "/thredds/dodsC/deployments/" + user + "/" + deployment + "/" + deployment + ".nc3.nc"
        return dap_url

    @hybrid_property
    def sos(self):
        '''
        Returns the URL to the NcSOS endpoint
        '''
        host = current_app.config['THREDDS']
        user = self.username
        deployment = self.name
        return "http://" + host + "thredds/sos/deployments/" + user + "/" + deployment + "/" + deployment + ".nc3.nc?service=SOS&request=GetCapabilities&AcceptVersions=1.0.0"

    @hybrid_property
    def iso(self):
        host = current_app.config['PRIVATE_ERDDAP']
        name = self.name
        return "http://" + host + "/erddap/tabledap/" + name + ".iso19115"

    @hybrid_property
    def thredds(self):
        host = current_app.config['THREDDS']
        user = self.username
        deployment = self.name
        return "http://" + host + "/thredds/catalog/deployments/" + user + "/" + deployment + "/catalog.html?dataset=deployments/" + user + "/" + deployment + "/" + deployment + ".nc3.nc"

    @hybrid_property
    def erddap(self):
        host = current_app.config['PRIVATE_ERDDAP']
        user = self.username
        deployment = self.name
        return "http://" + host + "/erddap/tabledap/" + deployment + ".html"

    @property
    def title(self):
        if self.operator is not None and self.operator != "":
            return self.operator
        else:
            return self.username

    @property
    def full_path(self):
        return os.path.join(current_app.config.get('DATA_ROOT'),
                            self.deployment_dir)

    @property
    def public_erddap_path(self):
        return os.path.join(current_app.config.get('PUBLIC_DATA_ROOT'),
                            self.deployment_dir)

    @property
    def thredds_path(self):
        return os.path.join(current_app.config.get('THREDDS_DATA_ROOT'),
                            self.deployment_dir)

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
                current_app.logger.info("Scheduling compliance check for completed "
                                "deployment {}".format(self.deployment_dir))
                current_app.queue.enqueue(glider_deployment_check,
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

    @email_exception_logging_wrapper
    def send_deployment_cchecker_email(self, user, failing_deployments, attachment_msgs):
        if not app.config.get('MAIL_ENABLED', False): # Mail is disabled
            app.logger.info("Email is disabled")
            return
        # sender comes from MAIL_DEFAULT_SENDER in env

        app.logger.info("Sending email about deployment compliance checker to {}".format(user['username']))
        subject        = "Glider DAC Compliance Check on Deployments for user %s" % user['username']
        recipients     = [user['email']] #app.config.get('MAIL_DEFAULT_TO')]
        msg            = Message(subject, recipients=recipients)
        if len(failing_deployments) > 0:
            message = ("The following glider deployments failed compliance check:"
                    "\n{}\n\nPlease see attached file for more details. "
                    "Valid CF standard names are required for NCEI archival."
                    .format("\n".join(d['name'] for d in failing_deployments)))
            date_str_today = datetime.today().strftime("%Y-%m-%d")
            attachment_filename = "failing_glider_md_{}".format(date_str_today)
            msg.attach(attachment_filename, 'text/plain', data=attachment_msgs)
        else:
            return
        msg.body       = message

        current_app.mail.send(msg)

    @email_exception_logging_wrapper
    def send_registration_email(self):
        current_app.logger.info("Sending email about new deployment to %s",
                                current_app.config.get('MAIL_DEFAULT_TO'))
        subject        = "New Glider Deployment - %s" % self.name
        recipients     = [current_app.config.get('MAIL_DEFAULT_TO')]
        cc_recipients  = []
        if current_app.config.get('MAIL_DEFAULT_LIST') is not None:
            cc_recipients.append(current_app.config.get('MAIL_DEFAULT_LIST'))

        message = Message(subject, recipients=recipients, cc=cc_recipients)
        message.body = render_template(
                            'deployment_registration.txt',
                            deployment=self,
                            username=self.username,
                            thredds_url=get_thredds_catalog_url(),
                            erddap_url=get_erddap_catalog_url())

        if not current_app.config.get('MAIL_ENABLED', False): # Mail is disabled
            current_app.logger.info("Email is disabled. Message digest below:")
            current_app.logger.info(message)
            return
        # sender comes from MAIL_DEFAULT_SENDER in env
        current_app.mail.send(message)

    def glider_deployment_check(self, data_type=None, completed=True, force=False,
                                deployment_dir=None, username=None):
        """
        """
        # TODO: move this functionality to another module as compliance checks
        #       no longer send emails.
        cs = CheckSuite()
        cs.load_all_available_checkers()
        query = Deployment.query
        with app.app_context():
            if data_type is not None:
                query = query.filter(Deployment.completed==completed,
                                                func.coalesce(Deployment.delayed_mode,
                                                            False) == is_delayed_mode)
                # TODO: force not null constraints in model on this field
                if not force:
                    query = query.filter(compliance_check_passed != True)

            if username:
                query = query.filter_by(username=username)
            # a particular deployment has been specified
            elif deployment_dir:
                query = query.filter_by(deployment_dir=deployment_dir)

        for deployment in query.all():
            user = deployment.username
            user_errors.setdefault(user, {"messages": [], "failed_deployments": []})

            try:
                dep_passed, dep_messages = self.process_deployment(deployment)
                if not dep_passed:
                    user_errors[user]["failed_deployments"].append(deployment.name)
                user_errors[user]["messages"].extend(dep_messages)
            except Exception as e:
                root_logger.exception("Exception occurred while processing deployment {}".format(deployment.name))

            # TODO: Allow for disabling of sending compliance checker emails
            for username, results_dict in user_errors.items():
                send_deployment_cchecker_email(username,
                                            results_dict["failed_deployments"],
                                            "\n".join(results_dict["messages"]))


class GeoJSONField(Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        # Convert GeoAlchemy geometry to GeoJSON format
        return geojson.loads(db.session.scalar(value.ST_AsGeoJSON()))


class DeploymentModelConverter(ModelConverter):
        SQLA_TYPE_MAPPING = {
            **ModelConverter.SQLA_TYPE_MAPPING
            #**{Geometry: Field}
        }

class DeploymentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Deployment
        model_converter = DeploymentModelConverter

    estimated_deploy_location = GeoJSONField()

    # TODO?: Aggressively Java-esque -- is there a better way to get these
    # hybrid properties?
    dap = Method("get_dap")
    sos = Method("get_sos")
    iso = Method("get_iso")
    thredds = Method("get_thredds")
    erddap = Method("get_erddap")

    def get_dap(self, obj):
        return obj.dap

    def get_sos(self, obj):
        return obj.sos

    def get_iso(self, obj):
        return obj.iso

    def get_thredds(self, obj):
        return obj.thredds

    def get_erddap(self, obj):
        return obj.erddap



    def process_deployment(self, deployment):
        deployment_issues = "Deployment {}".format(os.path.basename(deployment.name))
        groups = OrderedDict()
        erddap_fmt_string = "erddap/tabledap/{}.nc?&time%3Emax(time)-1%20day"
        base_url = app.config["PRIVATE_ERDDAP"]
        # FIXME: determine a more robust way of getting scheme
        if not base_url.startswith("http"):
            base_url = "http://{}".format(base_url)
        url_path = "/".join([base_url,
                            erddap_fmt_string.format(deployment.name)])
        # TODO: would be better if we didn't have to write to a temp file
        outhandle, outfile = tempfile.mkstemp()
        failures, _ = ComplianceChecker.run_checker(ds_loc=url_path,
                                    checker_names=['gliderdac'], verbose=True,
                                    criteria='lenient', output_format='json',
                                    output_filename=outfile)
        with open(outfile, 'r') as f:
            errs = json.load(f)["gliderdac"]

        compliance_passed = errs['scored_points'] == errs['possible_points']

        self.compliance_check_passed = compliance_passed
        standard_name_errs = []
        if compliance_passed:
            final_message = "All files passed compliance check on glider deployment {}".format(dep.name)
        else:
            error_list = [err_msg for err_severity in ("high_priorities",
                "medium_priorities", "low_priorities") for err_section in
                errs[err_severity] for err_msg in err_section["msgs"]]
            self.compliance_check_report = errs

            for err in errs["high_priorities"]:
                if err["name"] == "Standard Names":
                    standard_name_errs.extend(err["msgs"])

            if not standard_name_errs:
                final_message = "All files passed compliance check on glider deployment {}".format(deployment.name)
                self.cf_standard_names_valid = True
            else:
                root_logger.info(standard_name_errs)
                final_message = ("Deployment {} has issues:\n{}".format(dep.name,
                                "\n".join(standard_name_errs)))
                self.cf_standard_names_valid = False

        db.session.commit()
        return final_message.startswith("All files passed"), final_message

def on_models_committed(sender, changes):
    for model, operation in changes:
        if isinstance(model, Deployment):
            if operation == "insert" or operation == "update":
                if isinstance(model, (Deployment, User)):
                    model.save()
            elif operation == "delete":
                if isinstance(model, Deployment):
                    model.delete()
