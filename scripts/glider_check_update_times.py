import pymongo
import os
import multiprocessing
import glob
import logging
from netCDF4 import Dataset
# netcdftime was moving from main netCDF module
# try both here
import cftime
try:
    from cftime import utime
except ImportError:
    from netcdftime.netcdftime import utime
import numpy as np
import pandas as pd
import datetime
from pathlib import Path
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS


"""
A script to determine which netCDF files in various submission, public, and
private ERDDAP files might be lagging behind
"""

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)

logger = logging.getLogger("deployment_time_check")
logger.setLevel(logging.INFO)
logger.addHandler(ch)


def get_nc_time(nc_filepath):
    """
    Extract the netCDF time as pandas Timestamp
    or return NaT if the time can't be parsed
    """
    try:
        with Dataset(nc_filepath) as f:
            time_var = f.variables['profile_time']
            time_max = np.nanmax(time_var)
            time_calendar = getattr(time_var, 'calendar', 'gregorian')
            return pd.to_datetime(cftime.num2pydate(time_max, time_var.units, time_calendar))
    except Exception as e:
        logger.exception("Exception occurred during date handling for file {}".format(nc_filepath))
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
            logger.warning("FAILED: Comparison for '%s' %s vs %s not within %s",
                           label, t1[0], t2[0], check_thresh)
    except Exception as e:
        logger.exception()

def process_deployment(dep_subdir):
    """
    Processes deployments, comparing submissions to ERDDAP private
    and ERDDAP private to ERDDAP public
    """
    logger.info("Processing {}".format(dep_subdir))
    last_sub_time = get_last_nc_file(os.environ["SUBMISSION_DIR"], dep_subdir)
    last_priv_time = get_last_nc_file(os.environ["PRIV_ERDDAP_DIR"], dep_subdir)
    check_times(last_sub_time, last_priv_time, 'sub vs priv')
    return last_sub_time[1], last_priv_time[1]

def fetch_dataframe():
    """
    Returns a dataframe which executes comparisons times of deployments submitted,
    stored, and presently on ERDDAP
    """
    client = pymongo.MongoClient("{}:{}".format(
                                     os.getenv("MONGO_HOST", "localhost"),
                                     os.getenv("MONGO_PORT", "27017")))
    db = client.gliderdac
    comparison_df = pd.read_csv("https://gliders.ioos.us/erddap/tabledap/allDatasets.csv?datasetID%2CmaxTime",
                                index_col=0, header=0,
                                skiprows=[1, 2], names=["erddap_time"], parse_dates=[0])
    comparison_df.index.name = "dataset_name"

    # filter deployment time against last year
    updated_start_time = (datetime.datetime.utcnow() -
                          datetime.timedelta(days=365))
    dep_dict = {d["name"]: d["deployment_dir"] for d in
                db.deployments.find({'completed': False,
                                     'deployment_date': {"$gte": updated_start_time}},
                                     {'deployment_dir': True, 'name': True})}
    comparison_df["submission_time"] = pd.Series()
    comparison_df["priv_erddap_time"] = pd.Series()
    deployment_names = set(dep_dict.keys()).intersection(comparison_df.index)
    comparison_df = comparison_df.loc[deployment_names]
    for dep in deployment_names:
        deployment_ser = comparison_df.loc[dep]
        sub_time, priv_time = process_deployment(dep_dict[dep])
        comparison_df.loc[dep,
                          ["submission_time",
                            "priv_erddap_time"]] = [sub_time, priv_time]

    comparison_df["submission_time"] = \
            pd.to_datetime(comparison_df["submission_time"], utc=True)
    comparison_df["priv_erddap_time"] = \
            pd.to_datetime(comparison_df["priv_erddap_time"], utc=True)
    comparison_df["sub_diff"] = comparison_df["submission_time"] - comparison_df["erddap_time"]
    comparison_df["priv_diff"] = comparison_df["priv_erddap_time"] - comparison_df["erddap_time"]

    return comparison_df

def write_to_influxdb(df):
    """Writes the time data to InfluxDB"""
    try:
        client = InfluxDBClient(url=os.environ["INFLUXDB_URL"],
                                token="{}:{}".format(
                                        os.environ["INFLUX_USER"],
                                        os.environ["INFLUX_PASS"]),
                                org="GliderDAC", dbname="influx")
        _write_client = client.write_api(write_options=SYNCHRONOUS)
        df["_timestamp"] = pd.Timestamp.now(tz="utc")
        df = df.reset_index().set_index("_timestamp")
        # InfluxDB really doesn't like the timedelta columns, and claims
        # invalid timestamp
        del df["priv_diff"]
        del df["sub_diff"]
        _write_client.write(bucket="influx", record=df,
                            data_frame_measurement_name='erddap_nc_comparison',
                            data_frame_tag_columns=['dataset_name'],
                            time_precision="ns", protocol="line")
    except:
        logger.exception("Could not write values to InfluxDB")


def main():
    df = fetch_dataframe()

    erddap_file_diff_time = df["priv_diff"]
    # get files which need to be updated, namely any dataset in ERDDAP
    # application which lag their counterparts by more than two hours
    needs_updating = erddap_file_diff_time[erddap_file_diff_time >
                                           pd.Timedelta(2, "hours")]

    # touch flags for these old files so ERDDAP threads can kick
    # off an update at the next possible opportunity
    for ds_name in needs_updating.index:
        try:
            (Path(os.environ["FLAG_DIR"]) / ds_name).touch()
        except:
            logger.exception("Could not write flag file for deployment %s",
                             ds_name)
        else:
            logger.info("Created flag file for outdated deployment %s",
                        ds_name)

    # write metrics to InfluxDB
    write_to_influxdb(df)

if __name__ == '__main__':
    main()
