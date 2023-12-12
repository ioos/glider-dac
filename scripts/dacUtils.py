#!/usr/bin/env python
'''
scripts/dacUtils.py

A method to convert DAC 2.0 files into 1.0 files
'''
try:
    from netCDF4 import Dataset
    from netCDF4 import default_fillvals as NC_FILL_VALUES
except ImportError:
    import sys
    sys.stderr.write('Failed to import netCDF4, can not do 2.0 to 1.0 conversions')

import numpy as np
import os
import time
import sys
import argparse

def dacv2tov1(oldNc, newNc):

    # NetCDF4 compression level (1 seems to be optimal, in terms of effort and
    # result)
    COMP_LEVEL = 1

    # Depth-averaged current variables
    uvVars = ('time_uv', 'lat_uv', 'lon_uv', 'u', 'v', 'u_qc', 'v_qc',)
    # Dimensionless container variables
    containerVars = ('platform', 'instrument_ctd')

    # Open up the old file
    inFid = Dataset(oldNc, 'r')

    # Make sure we have a time variable
    if 'time' not in inFid.variables.keys():
        inFid.close()
        return ''

    # Open up the new file for writing
    outFid = Dataset(newNc, mode='w', clobber=True, format='NETCDF4_CLASSIC')

    # Copy all of the global attributes from inFid to outFid
    for attName in inFid.ncattrs():
        attValue = inFid.getncattr(attName)
        if attName == 'history':
            attValue = '{}\n{}: {}'.format(attValue, time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime()), os.path.abspath(__file__))
        elif attName == 'date_modified':
            attValue = time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime())
        elif attName == 'format_version':
            attValue = 'IOOS_Glider_NetCDF_v1.0.nc'

        outFid.setncattr(attName, attValue)

    # Get the length of the time data array
    tLength = len(inFid.variables['time'])
    uvLength = 1
    trajLength = 1

    # Create the dimensions of the 1.0 file
    outFid.createDimension('time', tLength)
    outFid.createDimension('trajectory', trajLength)
    outFid.createDimension('time_uv', uvLength)

    # Create the trajectory variable
    trajVar = outFid.createVariable('trajectory', inFid.variables['trajectory'].datatype, ('trajectory',))
    # Add the attributes
    for trajAtt in inFid.variables['trajectory'].ncattrs():
        if trajAtt == '_FillValue':
            continue

        trajVar.setncattr(trajAtt, inFid.variables['trajectory'].getncattr(trajAtt))

    # Add the data
    trajVar[:] = np.ones(1)

    # Loop through each of the variables in oldNc and create new variables in outNc
    # all variables that have 'time' as the dimension
    for varName, inVar in inFid.variables.items():

        # Must have 'time' as the dimension and the length of the variable data
        # array must be equal to tLength
        if 'time' not in inVar.dimensions:
            continue
        elif len(inVar) != tLength:
            print('time length error:', varName)
            continue

        # Create the variable
        outVar = outFid.createVariable(varName, inVar.datatype, inVar.dimensions)

        # Add the variable attributes
        for att in inVar.ncattrs():
            outVar.setncattr(att, inVar.getncattr(att))

        # Add the data
        outVar[:] = inVar[:]

    # Loop through each of the variables in uvVars and create the corresponding
    # variable, with attributes, in the new .nc file
    for varName in uvVars:

        if varName not in inFid.variables.keys():
            continue

        inVar = inFid.variables[varName]

        # Create the variable
        outVar = outFid.createVariable(varName, inVar.datatype, ('time_uv',))

        # Add the variable attributes
        for att in inVar.ncattrs():
            outVar.setncattr(att, inVar.getncattr(att))

        print(outVar.shape)
        print(inVar.shape)
        # Add the data
        outVar[:] = inVar[:]

    # Loop through each of the variables in uvVars and create the corresponding
    # variable, with attributes, in the new .nc file
    for varName in containerVars:

        if varName not in inFid.variables.keys():
            continue

        inVar = inFid.variables[varName]

        # Create the variable
        outVar = outFid.createVariable(varName, inVar.datatype)

        # Add the variable attributes
        for att in inVar.ncattrs():
            outVar.setncattr(att, inVar.getncattr(att))

    # PROFILE_ID
    # profile_id: 2 byte integer
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    profileId = outFid.createVariable('profile_id',
        'i2',
        ('time',),
        zlib=True,
        complevel=COMP_LEVEL,
        fill_value=NC_FILL_VALUES['i2'])
    # Dictionary of variable attributes.  Use a dictionary so that we can add the
    # attributes in alphabetical order (not necessary, but makes it easier to find
    # attributes that are in alphabetical order)
    atts = {'comment' : 'Sequential profile number within the current segment. A profile is defined as a single dive or climb', #  TODO: Revise definition'
        'long_name' : 'Profile ID',
        'valid_min' : 1,
        'valid_max' : 999,
        'observation_type' : 'calculated',
    }
    for k in sorted(atts.keys()):
        profileId.setncattr(k, atts[k])

    # Add the data (array of np.ones with the same length as tLength)
    profileId[:] = np.ones(tLength)

    # SEGMENT_ID
    # segment_id: 2 byte integer
    # kerfoot@marine.rutgers.edu: explicitly specify fill_value when creating
    # variable so that it shows up as a variable attribute.  Use the default
    # fill_value based on the data type.
    segmentId = outFid.createVariable('segment_id',
        'i2',
        ('time',),
        zlib=True,
        complevel=COMP_LEVEL,
        fill_value=NC_FILL_VALUES['i2'])
    atts = {'comment' : 'Sequential segment number within a trajectory/deployment. A segment corresponds to the set of data collected between 2 gps fixes obtained when the glider surfaces.',
        'long_name' : 'Segment ID',
        'valid_min' : 1,
        'valid_max' : 999,
        'observation_type' : 'calculated',
    }
    for k in sorted(atts.keys()):
        segmentId.setncattr(k, atts[k])

    inFid.close()
    outFid.close()

    return newNc

def main(args):
    if not os.path.exists(args.outputDirectory):
        if not args.MKDIR:
            sys.stderr.write('Invalid output directory: {0}\n'.format(args.outputDirectory))
            sys.exit(1)
        else:
            # Create it if the --mkdir option was specified and it does not exist
            print('Creating output directory:{0}\n'.format(args.outputDirectory))
            os.makedirs(args.outputDirectory)

    for oldNc in args.ncFiles:

        (oldPath, oldName) = os.path.split(oldNc)
        newNc = os.path.join(args.outputDirectory, oldName)

        nc = dacv2tov1(oldNc, newNc)

        print('File created:{0}\n'.format(newNc))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert one or more DAC 2.0 NetCDF files to version 1.0.  Output files use the same name as the input files.')
    parser.add_argument('outputDirectory',
        type=str,
        help='Destination directory for writing new files.')
    parser.add_argument('ncFiles',
        type=str,
        nargs='+',
        help='v2.0 files to process')
    parser.add_argument('-m', '--mkdir',
        action='store_true',
        dest='MKDIR',
        default=False,
        help='Create output directory if it does not exist')
    parser.add_argument('-c', '--clobber',
        action='store_true',
        dest='CLOBBER',
        default=False,
        help='Clobber existing file with the same name.')

    args = parser.parse_args()
    main(args)
