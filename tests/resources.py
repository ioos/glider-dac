import os
import subprocess


def get_filename(path):
    '''
    Returns the path to a valid dataset
    '''
    if not os.path.exists(path):
        cdl_path = path.replace('.nc', '.cdl')
        generate_dataset(cdl_path, path)
    return path


def generate_dataset(cdl_path, nc_path):
    '''
    Generates a netCDF file from a CDL file
    '''
    subprocess.call(['ncgen', '-o', nc_path, cdl_path])


STATIC_FILES = {
    'murphy': get_filename('test/data/Murphy-20150809T135508Z_rt/Murphy-20150809T135508Z_rt.nc'),
}
