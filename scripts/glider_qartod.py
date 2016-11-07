#!/usr/bin/env python
'''
scripts/glider_qartod.py
'''
from argparse import ArgumentParser
from netCDF4 import Dataset
from glider_qc.glider_qc import GliderQC
import sys
import logging


def main():
    '''
    Apply QARTOD QC to GliderDAC submitted netCDF files

    Example::

        python scripts/glider_qartod.py -c data/qc_config.yml ~/Desktop/revellie/revellie.nc

    '''
    logging.basicConfig(level=logging.INFO)
    parser = ArgumentParser(description=main.__doc__)
    parser.add_argument('-c', '--config', help='Path to config YML file to use')
    parser.add_argument('netcdf_files', nargs='+', help='NetCDF file to apply QC to')

    args = parser.parse_args()
    for nc_path in args.netcdf_files:
        print nc_path
        with Dataset(nc_path, 'r+') as nc:
            run_qc(args.config, nc)
    sys.exit(0)


def run_qc(config, ncfile):
    '''
    Runs QC on a netCDF file
    '''
    qc = GliderQC(ncfile, config)
    for varname in qc.find_geophysical_variables():
        ncvar = ncfile.variables[varname]
        if not qc.needs_qc(ncvar):
            continue
        for qcvarname in qc.create_qc_variables(ncvar):
            qcvar = ncfile.variables[qcvarname]
            qc.apply_qc(qcvar)
        qc.apply_primary_qc(ncvar)


if __name__ == '__main__':
    main()
