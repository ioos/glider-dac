#!/usr/bin/env python
'''
scripts/glider_qartod.py
'''
from argparse import ArgumentParser
from netCDF4 import Dataset
from glider_qc.glider_qc import GliderQC, log
import sys
import logging


def main():
    '''
    Apply QARTOD QC to GliderDAC submitted netCDF files

    Example::

        python scripts/glider_qartod.py -c data/qc_config.yml ~/Desktop/revellie/revellie.nc

    '''
    parser = ArgumentParser(description=main.__doc__)
    parser.add_argument('-c', '--config', help='Path to config YML file to use')
    parser.add_argument('-v', '--verbose', action='store_true', help='Turn on logging')
    parser.add_argument('netcdf_files', nargs='+', help='NetCDF file to apply QC to')

    args = parser.parse_args()
    if args.verbose:
        setup_logging()
    for nc_path in args.netcdf_files:
        with Dataset(nc_path, 'r') as nc:
            if not check_needs_qc(nc):
                continue

        log.info("Applying QC to dataset %s", nc_path)
        with Dataset(nc_path, 'r+') as nc:
            run_qc(args.config, nc)
    sys.exit(0)


def check_needs_qc(ncfile):
    '''
    Returns True if the netCDF file needs GliderQC
    '''
    qc = GliderQC(ncfile, None)
    for varname in qc.find_geophysical_variables():
        ncvar = ncfile.variables[varname]
        if qc.needs_qc(ncvar):
            return True
    return False


def run_qc(config, ncfile):
    '''
    Runs QC on a netCDF file
    '''
    qc = GliderQC(ncfile, config)
    for varname in qc.find_geophysical_variables():
        log.info("Inspecting %s", varname)
        ncvar = ncfile.variables[varname]

        if not qc.needs_qc(ncvar):
            log.info("%s does not need QARTOD", varname)
            continue

        for qcvarname in qc.create_qc_variables(ncvar):
            log.info("Created QC Variable %s", qcvarname)
            qcvar = ncfile.variables[qcvarname]

            log.info("Applying QC for %s", qcvar.name)
            qc.apply_qc(qcvar)

        qc.apply_primary_qc(ncvar)


def setup_logging(
    default_path=None,
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration
    """
    logging.basicConfig(level=default_level)

if __name__ == '__main__':
    main()
