import pymongo
import os
import multiprocessing
import glob
import logging
from glider_dac import app
from netCDF4 import Dataset
# netcdftime was moving from main netCDF module
# try both here
try:
    from cftime import utime
except ImportError:
    from netcdftime.netcdftime import utime
import numpy as np
import pandas as pd
from glider_dac import app
from datetime import datetime
from influxdb import InfluxDBClient


"""
A script to determine which netCDF files in various submission, public, and
private ERDDAP files might be lagging behind
"""

# TODO: Add actual logging instead of print statements
logger = logging.basicConfig()


def get_nc_time(nc_filepath):
    """
    Extract the netCDF time as pandas Timestamp
    or return NaT if the time can't be parsed
    """
    try:
        with Dataset(nc_filepath) as f:
            time_var = f.variables['time']
            time_raw = time_var[-1]
            time_units = time_var.units
            time_calendar = getattr(time_var, 'calendar', 'gregorian')
        time_conv = utime(time_units, time_calendar)

        return pd.to_datetime(time_conv.num2date(time_raw))
    except Exception as e:
        print(str(e))
        return pd.NaT

def get_last_nc_file(root_folder, subdir):
    """
    Try to find the last netCDF file and time based on sorted filename and
    file modification time.  If the two don't match, read the netCDF file
    and find the file with the last time.  Return a 2-tuple with the filename
    and the last time variable value contained in the netCDF file
    """
    sub_files_glob = os.path.join(root_folder, subdir, '*.nc')
    sub_files = glob.glob(sub_files_glob)
    try:
        last_name = sorted(sub_files)[-1]
        last_mod_time = sorted(sub_files, key=os.path.getmtime)[-1]
    # if IndexError is thrown, there are no netCDF files present
    except IndexError:
        return None

    # if both files names are the same, return them both
    if last_name == last_mod_time:
        return last_name, get_nc_time(last_name)
    # otherwise find the file with the last time
    else:
        tiebreaker = pd.Series({last_name: get_nc_time(last_name),
                                last_mod_time: get_nc_time(last_mod_time)})

        if pd.isnull(tiebreaker).all():
            print('All times for {} and {} are bad, nonexistent, or cannot be read'.format(last_name, last_mod_time))
            return None
        else:
            max_label = tiebreaker.idxmax()
            return max_label, tiebreaker[max_label]


def check_times(t1, t2, label, check_thresh=pd.Timedelta(hours=12)):
    try:
        td = t1[1] - t2[1]
        if td > check_thresh:
            print("FAILED: Comparison for '{}' {} vs {} not within {}".format(label,
                                                                            t1[0],
                                                                            t2[0],
                                                                            check_thresh))
            print(t1[1], t2[1])
    except Exception as e:
        print(str(e))

def process_deployment(dep_subdir):
    """
    Processes deployments, comparing submissions to ERDDAP private
    and ERDDAP private to ERDDAP public
    """
    print(dep_subdir)
    last_sub_time = get_last_nc_file(app.config["DATA_ROOT"], dep_subdir)
    last_priv_time = get_last_nc_file(app.config["PRIV_ERDDAP_ROOT"],
                                      dep_subdir)
    last_pub_time = get_last_nc_file(app.config["PUBLIC_DATA_ROOT"], dep_subdir)
    check_times(last_sub_time, last_priv_time, 'sub vs priv')
    check_times(last_priv_time, last_pub_time, 'priv vs pub')
    try:
        # TODO: Batch writes, but add better error protection so that issues don't cause whole
        #       write to fail.
        data = {"measurement": "erddap_nc_comparison",
                "tags": {
                        "deployment": dep_subdir.rsplit("/", 1)[-1]
                        },
                    "time": current_time.isoformat(),
                    "fields": {
                        "erddap_time": int(last_pub_time[1].to_pydatetime().strftime("%s")),
                        "priv_erddap_time": int(last_priv_time[1].to_pydatetime().strftime("%s")),
                        "submission_time": int(last_sub_time[1].to_pydatetime().strftime("%s"))
                    }
                }
        influx_client.write_points([data], database='influx')
    except Exception as e:
        print(str(e))



if __name__ == '__main__':
    client = pymongo.MongoClient("{}:{}".format(app.config["MONGODB_HOST"],
                                                app.config["MONGODB_PORT"]))
    db = client.gliderdac
    dep_list = [d['deployment_dir'] for d in
                db.deployments.find({}, {'deployment_dir': True})]
    #influx_client = InfluxDBClient(host=app.config.get("INFLUXDB_HOST", "localhost"),
    #                        port=8086)
    influx_client = InfluxDBClient(host=app.config["INFLUXDB_HOST"],
                                   port=app.config["INFLUXDB_PORT"])
    current_time = datetime.utcnow()
    pool = multiprocessing.Pool()
    pool.map(process_deployment, dep_list)
