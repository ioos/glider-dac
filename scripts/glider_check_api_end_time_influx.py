import pymongo
import os
import multiprocessing
import glob
import logging
import requests
from glider_dac import app
from netCDF4 import Dataset
from cftime import utime
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from influxdb import InfluxDBClient

"""
Script to push submission/ERDDAP times + Glider API start/end times
into InfluxDB database `glider_end_time`, measurement `glider_data`.
"""

logger = logging.basicConfig()
current_time = datetime.utcnow()


def get_nc_time(nc_filepath):
    """Extract last netCDF time as pandas Timestamp"""
    try:
        with Dataset(nc_filepath) as f:
            time_var = f.variables['time']
            time_raw = time_var[-1]
            time_units = time_var.units
            time_calendar = getattr(time_var, 'calendar', 'gregorian')
        time_conv = utime(time_units, time_calendar)
        return time_conv.num2date(time_raw)._to_real_datetime()
    except Exception as e:
        print(f"Error reading {nc_filepath}: {e}")
        return pd.NaT


def get_last_nc_file(root_folder, subdir):
    """Find last netCDF file by filename or mod time"""
    sub_files_glob = os.path.join(root_folder, subdir, '*.nc')
    sub_files = glob.glob(sub_files_glob)
    try:
        last_name = sorted(sub_files)[-1]
        last_mod_time = sorted(sub_files, key=os.path.getmtime)[-1]
    except IndexError:
        return None

    if last_name == last_mod_time:
        return last_name, get_nc_time(last_name)
    else:
        tiebreaker = pd.Series({
            last_name: get_nc_time(last_name),
            last_mod_time: get_nc_time(last_mod_time)
        })
        if pd.isnull(tiebreaker).all():
            print(f"All times bad for {last_name} and {last_mod_time}")
            return None
        max_label = tiebreaker.idxmax()
        return max_label, tiebreaker[max_label]


def get_erddap_server_time(deployment):
    """Fetch max precise_time from ERDDAP for deployment"""
    erddap_loc = (f"https://{app.config['SERVER_NAME']}/erddap/"
                  f"tabledap/{deployment.split('/')[-1]}.csv"
                   "?precise_time&precise_time=max(precise_time)")
    try:
        df = pd.read_csv(erddap_loc, skiprows=1, parse_dates=[0])
        return df.iloc[0, 0].timestamp()
    except Exception as e:
        print(f"ERDDAP error {deployment}: {e}")
        return None


def get_glider_api_times(identifier):
    """Get start_time and end_time from Glider Map API for identifier"""
    api_url = "https://gliders.ioos.us/map/api/catalog"
    try:
        resp = requests.get(api_url, timeout=20, verify=False)
        resp.raise_for_status()
        data = resp.json()

        for record in data.get("records", []):
            if record.get("identifier") == identifier:
                return record.get("start_time"), record.get("end_time")
            for child in record.get("children", []):
                if child.get("identifier") == identifier:
                    return child.get("start_time"), child.get("end_time")
    except Exception as e:
        print(f"Glider API error {identifier}: {e}")
    return None, None


def process_deployment(dep_subdir):
    print(f"Processing {dep_subdir}")
    identifier = dep_subdir.rsplit("/", 1)[-1] #Assumption  folder name is identifier

    last_sub_time = get_last_nc_file(app.config["DATA_ROOT"], dep_subdir)
    last_priv_time = get_last_nc_file(app.config["PRIV_DATA_ROOT"], dep_subdir)
    last_pub_time = get_last_nc_file(app.config["PUBLIC_DATA_ROOT"], dep_subdir)
    erddap_server_time = get_erddap_server_time(dep_subdir)
    start_time, end_time = get_glider_api_times(identifier)  # getting start and end time from api

    data = {
        "measurement": "glider_data",   
        "tags": {
            "identifier": identifier
        },
        "time": current_time.isoformat(),
        "fields": {}
    }

    if last_pub_time is not None:
        data["fields"]["erddap_time"] = last_pub_time[1].timestamp()
    if last_priv_time is not None:
        data["fields"]["priv_erddap_time"] = last_priv_time[1].timestamp()
    if last_sub_time is not None:
        data["fields"]["submission_time"] = last_sub_time[1].timestamp()
    if erddap_server_time is not None:
        data["fields"]["erddap_server_time"] = erddap_server_time
    if start_time:
        try:
            ts_start = datetime.fromisoformat(start_time).timestamp()
            data["fields"]["start_time"] = ts_start
            data["fields"]["initial_submission_time"] = ts_start
        except Exception as e:
            print(f"Start time parse error {identifier}: {e}")
    if end_time:
        try:
            data["fields"]["end_time"] = datetime.fromisoformat(end_time).timestamp()
        except Exception as e:
            print(f"End time parse error {identifier}: {e}")

    if not data["fields"]:
        print(f"No valid fields for {identifier}, skipping")
        return

    try:
        influx_client.write_points([data], database='glider_end_time', protocol="json")  # writing to new DB glider_end_time in influxdb
        print(f"Wrote data for {identifier}")
    except Exception as e:
        print(f"Influx write error {identifier}: {e}")

if __name__ == '__main__':
    client = pymongo.MongoClient("{}:{}".format(app.config["MONGODB_HOST"],
                                                app.config["MONGODB_PORT"]))
    db = client.gliderdac
    dt_filt = current_time - timedelta(days=270)
    dep_list = [d['deployment_dir'] for d in
                db.deployments.find({'completed': False,
                                     'updated': {"$gt": dt_filt}},
                                     {'deployment_dir': True})]

    influx_client = InfluxDBClient(host=app.config["INFLUXDB_HOST"],
                                   port=app.config["INFLUXDB_PORT"])
    pool = multiprocessing.Pool()
    pool.map(process_deployment, dep_list)
