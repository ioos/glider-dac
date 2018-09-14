import pymongo
import os
import multiprocessing
import glob
import logging
from netCDF4 import Dataset
# netcdftime was moving from main netCDF module
# try both here
try:
    from cftime import utime
except ImportError:
    from netcdftime.netcdftime import utime
import numpy as np
import pandas as pd


"""
A script to determine which netCDF files in various submission, public, and
private ERDDAP files might be lagging behind
"""

SUBMISSION_FOLDER = '/data/submission'
PRIV_ERDDAP_FOLDER = '/data/data/priv_erddap'
PUB_ERDDAP_FOLDER = '/data/data/pub_erddap'

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
        if td <= check_thresh:
            pass
            #print("Comparison for '{}' {} vs {} within {}".format(label,
            #                                                    t1[0], t2[0],
            #                                                    check_thresh))
        else:
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
    last_sub_time = get_last_nc_file(SUBMISSION_FOLDER, dep_subdir)
    last_priv_time = get_last_nc_file(PRIV_ERDDAP_FOLDER, dep_subdir)
    last_pub_time = get_last_nc_file(PUB_ERDDAP_FOLDER, dep_subdir) 
    check_times(last_sub_time, last_priv_time, 'sub vs priv')
    check_times(last_priv_time, last_pub_time, 'priv vs pub')



if __name__ == '__main__':
    client = pymongo.MongoClient('localhost:27017')
    db = client.gliderdac
    dep_list = [d['deployment_dir'] for d in
                db.deployments.find({}, {'deployment_dir': True})]
    pool = multiprocessing.Pool()
    pool.map(process_deployment, dep_list)
