#!/usr/bin/env python
import os
import time
import json
import argparse
import logging
import fileinput
import glob
from string import Template
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, DirCreatedEvent, FileModifiedEvent, DirModifiedEvent
from watchdog.observers import Observer
from threading import Lock, Timer
from lxml import etree

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s | %(levelname)s]  %(message)s')
logger = logging.getLogger(__name__)

RSYNC_TO_PATH         = os.environ.get("RSYNC_TO_PATH")
CATALOG_ROOT          = os.environ.get("CATALOG_ROOT")
DATA_ROOT             = os.environ.get("DATA_ROOT")
PRIV_ERDDAP_TEMPLATES = os.environ.get("PRIV_ERDDAP_TEMPLATES")
PUB_ERDDAP_TEMPLATES  = os.environ.get("PUB_ERDDAP_TEMPLATES")

class HandleDeployment(FileSystemEventHandler):
    def __init__(self, base, catalog, data_root, priv_erddap_templates, pub_erddap_templates):
        self.base                  = base
        self.catalog               = catalog
        self.data_root             = data_root
        self.priv_erddap_templates = priv_erddap_templates
        self.pub_erddap_templates  = pub_erddap_templates

        self.lock                  = Lock()
        self.timers                = {}

    def _schedule(self, rel_path, path_parts):
        with self.lock:
            if rel_path in self.timers:
                logger.info("Cancelling existing timer for %s", rel_path)
                t = self.timers.pop(rel_path)
                t.cancel()

            logger.info("Scheduling timer for %s", rel_path)
            self.timers[rel_path] = Timer(5, self._sync_catalogs, args=[rel_path, path_parts[0], path_parts[1]])
            self.timers[rel_path].start()

    def _sync_catalogs(self, rel_path, user, deployment):
        """
        Synchronize all aspects of the catalog machine.

        Makes calls to
        - Ensure directories are present
        - Build private/public erddap catalogs
        - Build TDS catalogs
        - Refresh anything
        """
        with self.lock:
            self.timers.pop(rel_path)

        self._make_all_dirs(rel_path, user, deployment)
        self._build_erddap_catalog_fragment(rel_path, user, deployment, 'priv_erddap', self.priv_erddap_templates)
        #self._build_erddap_catalog_fragment(rel_path, user, deployment, 'pub_erddap', self.pub_erddap_templates)
        #self._build_thredds_catalog(rel_path, user, deployment)

        # schedule a full catalog build out of the parts
        self._schedule_catalog_assembly()

    def _schedule_catalog_assembly(self):
        full = 'full_catalog_asm'
        with self.lock:
            if full in self.timers:
                t = self.timers.pop(full)
                t.cancel()

            logger.info("Scheduling timer for full catalog rebuild")
            self.timers[full] = Timer(5, self._assemble_catalogs)
            self.timers[full].start()

    def _assemble_catalogs(self):
        """
        Builds a full ERDDAP datasets.xml for both pub/private, and a TDS catalog (??)
        """
        self._assemble_erddap_catalog('priv_erddap', self.priv_erddap_templates)
        self._assemble_erddap_catalog('pub_erddap', self.pub_erddap_templates)
        self._assemble_thredds_catalog()

    def _assemble_erddap_catalog(self, erddap_name, template_dir):
        """
        Cats together the head, all fragments, and foot of a datasets.xml
        """
        head_path = os.path.join(template_dir, 'datasets.head.xml')
        tail_path = os.path.join(template_dir, 'datasets.tail.xml')

        # discover all filenames of dataset fragments
        pattern = os.path.join(self.catalog, erddap_name, 'fragment-*')
        fragment_files = glob.glob(pattern)

        fragment_files.insert(0, head_path)
        fragment_files.append(tail_path)

        ds_path = os.path.join(self.catalog, erddap_name, 'datasets.xml')
        with open(ds_path, 'w') as f:
            for line in fileinput.input(fragment_files):
                f.write(line)

        logger.info("Wrote %s from %d files", ds_path, len(fragment_files))

    def _assemble_thredds_catalog(self):
        pass

    def _make_all_dirs(self, rel_path, user, deployment):
        """
        Ensures all directories are created for a user/deployment.

        - private/public erddap data roots
        - tds data root
        """
        if not self.data_root:
            raise StandardError("NO DATA ROOT")

        for dir_suffix in ["priv_erddap", "pub_erddap", "thredds"]:
            d = os.path.join(self.data_root, dir_suffix, user, deployment)

            if not os.path.exists(d):
                logger.info("Creating %s", d)
                try:
                    os.makedirs(d)
                except OSError:
                    pass

    def _build_thredds_catalog(self, rel_path, user, deployment):
        """
        Creates THREDDS catalog files for the given user/deployment.
        """
        logger.info("Creating Thredds catalog and NcML Aggregations for %s", rel_path)
        self._create_ncml(user=user, deployment=deployment)
        self._create_catalog(user=user, deployment=deployment)

    def on_created(self, event):

        rel_path = os.path.relpath(event.src_path, self.base)
        path_parts = rel_path.split(os.sep)

        # expecting a user/deployment
        if isinstance(event, DirCreatedEvent) and len(path_parts) == 2:
            logger.info("New deployment directory: %s", rel_path)
            self._schedule(rel_path, path_parts)

        # expecting a user/deployment/file
        elif isinstance(event, FileCreatedEvent) and len(path_parts) != 3 and path_parts[-1] == "deployment.json":
            logger.info("Creating Catalog and NcML Aggregations with new Deployment metadata")
            self._schedule(rel_path, path_parts)

    def on_modified(self, event):

        rel_path = os.path.relpath(event.src_path, self.base)
        path_parts = rel_path.split(os.sep)

        # expecting a user/deployment
        if isinstance(event, DirModifiedEvent) and len(path_parts) == 2:
            logger.info("Directory modified: %s", rel_path)
            logger.info("Recreating catalog and NcML Aggregations")
            self._schedule(rel_path, path_parts)

        # expecting a user/deployment/file
        elif isinstance(event, FileModifiedEvent) and len(path_parts) == 3 and path_parts[-1] == "deployment.json":
            logger.info("Recreating Catalog and NcML Aggregations with modified Deployment metadata")
            self._schedule(rel_path, path_parts)

    def _build_erddap_catalog_fragment(self, rel_path, user, deployment, erddap_name, template_dir):
        """
        Builds an ERDDAP dataset xml fragment.
        """
        logger.info("Building ERDDAP (%s) catalog fragment for %s", erddap_name, rel_path)

        # grab template for dataset fragment
        template_path = os.path.join(template_dir, 'dataset.deployment.xml')
        with open(template_path) as f:
            template = Template("".join(f.readlines()))

        # grab institution, if we can find one
        institution     = user
        deployment_name = deployment
        dir_path        = os.path.join(self.base, user, deployment)
        try:
            with open(os.path.join(dir_path, "deployment.json")) as f:
                js              = json.load(f)
                institution     = js.get('operator', js.get('username'))
                deployment_name = js['name']
                wmo_id          = js['wmo_id'].strip()
        except (OSError, IOError, AssertionError, AttributeError):
            pass

        frag_path = os.path.join(self.catalog, erddap_name, 'fragment-' + deployment + '.xml')
        with open(frag_path, 'w') as f:
            f.writelines(template.substitute(dataset_id=deployment,
                                             dataset_dir=dir_path,
                                             institution=institution))

    def _create_catalog(self, user, deployment):

        dir_path    = os.path.join(self.base, user, deployment)
        cat_path    = os.path.join(self.catalog, 'thredds', user, deployment)

        time_path   =  os.path.join(cat_path, "timeagg.ncml")
        timeuv_path =  os.path.join(cat_path, "timeuvagg.ncml")

        # Load Misson JSON if is exists.  We want to pull information from this JSON
        # and not rely on the directory structure if possible.
        title        = user
        deployment_name = deployment
        wmo_id       = "NotAssigned"
        try:
          with open(os.path.join(dir_path, "deployment.json")) as f:
            js           = json.load(f)
            title        = js['operator']
            if title is None or title == "":
              title = js['username']
            deployment_name = js['name']
            wmo_id       = js['wmo_id'].strip()
        except (OSError, IOError, AssertionError, AttributeError):
          pass
        finally:
          title        = slugify(title)
          deployment_name = slugify(deployment_name)

        try:
            os.makedirs(cat_path)
        except OSError:
            # Dir Already exists
            pass

        cat_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <catalog name="IOOS Glider DAC - %(title)s - %(deployment)s Catalog"
         xmlns="http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"
         xmlns:xlink="http://www.w3.org/1999/xlink">

          <service name="agg" base="" serviceType="compound">
            <service name="odap" serviceType="OpenDAP" base="/thredds/dodsC/" />
            <service name="ncml" serviceType="NCML" base="/thredds/ncml/" />
            <service name="uddc" serviceType="UDDC" base="/thredds/uddc/" />
            <service name="iso" serviceType="ISO" base="/thredds/iso/"/>
            <service name="sos" serviceType="SOS" base="/thredds/sos/" />
          </service>

          <dataset name="%(title)s - %(deployment_name)s - Time Aggregation" ID="%(title)s_%(deployment_name)s_Time" urlPath="%(title)s_%(deployment_name)s_Time.ncml">
            <serviceName>agg</serviceName>
            <netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2" location="%(time_path)s" />
          </dataset>

          <dataset name="%(title)s - %(deployment_name)s - Depth Averaged Aggregation" ID="%(title)s_%(deployment_name)s_TimeUV" urlPath="%(title)s_%(deployment_name)s_TimeUV.ncml">
            <serviceName>agg</serviceName>
            <netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2" location="%(timeuv_path)s" />
          </dataset>
        </catalog>
        """ % locals()

        with open(os.path.join(cat_path, "catalog.xml"), 'w') as f:
            f.write(cat_xml)

        # create individual files catalog
        cat_indv_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <catalog name="IOOS Glider DAC - %(title)s - %(deployment)s Catalog (Individual Files)"
         xmlns="http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"
         xmlns:xlink="http://www.w3.org/1999/xlink">

          <service name="all" base="" serviceType="compound">
            <service name="odap" serviceType="OpenDAP" base="/thredds/dodsC/" />
            <service name="http" serviceType="HTTPServer" base="/thredds/fileServer/" />
            <service name="ncml" serviceType="NCML" base="/thredds/ncml/" />
            <service name="uddc" serviceType="UDDC" base="/thredds/uddc/" />
            <service name="iso" serviceType="ISO" base="/thredds/iso/"/>
            <service name="sos" serviceType="SOS" base="/thredds/sos/" />
          </service>

          <datasetScan name="%(title)s - %(deployment_name)s - Individual Files" ID="%(title)s_%(deployment_name)s_Files" path="%(title)s_%(deployment_name)s_Files" location="%(dir_path)s">
            <metadata inherited="true">
              <serviceName>all</serviceName>
            </metadata>
            <filter>
              <include wildcard="*.nc"/>
            </filter>
            <netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">
              <variable name="platform">
                <attribute name="wmo_id" value="%(wmo_id)s" />
              </variable>
            </netcdf>
          </datasetScan>
        </catalog>
        """ % locals()

        with open(os.path.join(cat_path, "catalog-individual.xml"), 'w') as f:
            f.write(cat_indv_xml)

    def _create_ncml(self, user, deployment):

        dir_path = os.path.join(self.base, user, deployment)
        cat_path = os.path.join(self.catalog, 'thredds', user, deployment)

        try:
            os.makedirs(cat_path)
        except OSError:
            # Dir Already exists
            pass

        # Add WMO ID if it exists
        try:
          with open(os.path.join(dir_path, "deployment.json")) as f:
            js     = json.load(f)
            wmo_id = js['wmo_id'].strip()
            assert len(wmo_id) > 0
        except (IOError, AssertionError, AttributeError):
          # No wmoid.txt file
          wmo_id = "NotAssigned"

        time_agg = """<?xml version="1.0" encoding="UTF-8"?>
            <netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">
              <remove type="variable" name="time_uv"/>
              <remove type="variable" name="lat_uv"/>
              <remove type="variable" name="lon_uv"/>
              <remove type="variable" name="u"/>
              <remove type="variable" name="u_qc"/>
              <remove type="variable" name="v_qc"/>

              <variable name="platform">
                <attribute name="wmo_id" value="%(wmo_id)s" />
              </variable>

              <aggregation dimName="time" type="joinExisting" recheckEvery="5 min">
                <scan location="%(dir_path)s" suffix=".nc" subdirs="false" />
              </aggregation>
            </netcdf>
            """ % locals()

        with open(os.path.join(cat_path, "timeagg.ncml"), 'w') as f:
            f.write(time_agg)


        time_uv_agg = """<?xml version="1.0" encoding="UTF-8"?>
            <netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">
              <remove type="variable" name="time"/>
              <remove type="variable" name="time_qc"/>
              <remove type="variable" name="segment_id"/>
              <remove type="variable" name="profile_id"/>
              <remove type="variable" name="depth"/>
              <remove type="variable" name="depth_qc"/>
              <remove type="variable" name="lat"/>
              <remove type="variable" name="lat_qc"/>
              <remove type="variable" name="lon"/>
              <remove type="variable" name="lon_qc"/>
              <remove type="variable" name="pressure"/>
              <remove type="variable" name="pressure_qc"/>
              <remove type="variable" name="conductivity"/>
              <remove type="variable" name="conductivity_qc"/>
              <remove type="variable" name="density"/>
              <remove type="variable" name="density_qc"/>
              <remove type="variable" name="salinity"/>
              <remove type="variable" name="salinity_qc"/>
              <remove type="variable" name="temperature"/>
              <remove type="variable" name="temperature_qc"/>

              <variable name="platform">
                <attribute name="wmo_id" value="%(wmo_id)s" />
              </variable>

              <aggregation dimName="time_uv" type="joinExisting" recheckEvery="5 min">
                <scan location="%(dir_path)s" suffix=".nc" subdirs="false" />
              </aggregation>
            </netcdf>
            """ % locals()

        with open(os.path.join(cat_path, "timeuvagg.ncml"), 'w') as f:
            f.write(time_uv_agg)

def slugify(value):
    """
    Normalizes string, removes non-alpha characters, and converts spaces to hyphens.
    Pulled from Django
    """
    import unicodedata
    import re
    value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip())
    return unicode(re.sub('[-\s]+', '-', value))

def main(handler):
    observer = Observer()
    observer.schedule(handler, path=handler.base, recursive=True)
    observer.start()
    logger.info("Watching user directories in %s", handler.base)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('basedir',
                        default=RSYNC_TO_PATH,
                        nargs='?')
    parser.add_argument('catalogdir',
                        default=CATALOG_ROOT,
                        nargs='?')
    parser.add_argument('data_root',
                        default=DATA_ROOT,
                        nargs='?')
    parser.add_argument('priv_erddap_templates',
                        default=PRIV_ERDDAP_TEMPLATES,
                        nargs='?')
    parser.add_argument('pub_erddap_templates',
                        default=PUB_ERDDAP_TEMPLATES,
                        nargs='?')

    args = parser.parse_args()

    base                  = os.path.realpath(args.basedir)
    catalog               = os.path.realpath(args.catalogdir)
    data_root             = os.path.realpath(args.data_root)
    priv_erddap_templates = os.path.realpath(args.priv_erddap_templates)
    pub_erddap_templates  = os.path.realpath(args.pub_erddap_templates)

    main(HandleDeployment(base, catalog, data_root, priv_erddap_templates, pub_erddap_templates))

