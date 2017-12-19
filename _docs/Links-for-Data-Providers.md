---
title: "HOMEPAGE [First Document]"
keywords: homepage
tags: [getting_started, about, overview]
#sidebar: home_sidebar
sidebar: mydoc_sidebar
topnav: topnav
toc: false
#permalink: index.html
summary: This is a Markdown document that will be rendered as the site 2nd page 
---

## [Wiki](https://github.com/kerfoot/ioosngdac/wiki)  **Data Provider Links**

The following is a list of links for data providers and web applications developers that provide the means to create new deployments, upload conforming [DAC NetCDF files](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2), view data set status and programmatically interface with the DAC via a RESTful API.

# Contents

- [Utilities and Resources for Data Providers](#utilities-and-resources-for-data-providers)
- [Links](#links)
- [Interacting with the DAC](#link-use-and-descriptions)

## Utilities and Resources for Data Providers
The following is a list of useful scripts and utilities for registered and prospective data providers

- [Simple DAC NetCDF File Validator](https://github.com/kerfoot/nc-validate)
    This python script compares a list of one or more NetCDF files to a known conforming [DAC NetCDF file](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2) and prints the results to STDOUT and STDERR.  If your files validate against this script they will be accepted by the DAC.  It is <b>highly recommended</b> that you use this script to help you check your [DAC NetCDF files](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2) before submitting them as it will significantly decrease your development time.  This script requires the following non-core modules:
    + [Python netcdf4](http://netcdf4-python.googlecode.com/svn/trunk/docs/netCDF4-module.html)
- [FTP script](https://github.com/ioos/ioosngdac/blob/master/util/ncFtp2ngdac.pl) for automating uploads of [conforming](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2) NetCDF files to the DAC ftp server.  The script is written in Perl and requires the following non-core modules:
    + [Readonly](http://search.cpan.org/~roode/Readonly-1.03/Readonly.pm)
    + [Net::FTP](http://search.cpan.org/~shay/libnet-1.25/Net/FTP.pm)

## Links
The following is a list of links that will take you directly to the specified resource.

- __Deployment Registration__: http://data.ioos.us/gliders/providers
- __NetCDF FTP server__: ftp://data.ioos.us/
- __Data Set Status__: https://gliders.ioos.us/status/
- __DAC RESTful API__: http://data.ioos.us/gliders/providers/api/deployment
- __ERDDAP Data Set Access__: http://data.ioos.us/gliders/erddap/tabledap/index.html
- __THREDDS Data Set Access__: http://data.ioos.us/gliders/thredds/catalog.html
- __IOOS Gliders and the DAC__: https://gliders.ioos.us/data
- __IOOS Catalog Map__: https://gliders.ioos.us/map/

## Link Use and Descriptions
- [Deployment Registration](#deployment-registration)
- [NetCDF FTP server](#netcdf-ftp-server)
- [Data Set Status](#data-set-status)
- [DAC RESTful API](#dac-restful-api)
- [ERDDAP Data Set Access](#erddap-data-set-access)
- [THREDDS Data Set Access](#thredds-data-set-access)
- [IOOS Gliders and the DAC](#ioos-gliders-and-the-dac)
- [IOOS Catalog Map](#ioos-catalog-map)

### Deployment Registration

### NetCDF-ftp-server

### Data Set Status

### ERDDAP Data Set Access

### THREDDS Data Set Access

### IOOS Gliders and the DAC

### IOOS Catalog Map
