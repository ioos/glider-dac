---
title: Links for Data Providers
wikiPageName: Links-for-Data-Providers
keywords: IOOS, documentation
tags: [getting_started, about, overview]
toc: false
#search: exclude
#permalink: index.html
summary: A list of links for Data Providers
---

<!--
> [Wiki](https://github.com/kerfoot/ioosngdac/wiki) ▸ **Data Provider Links**
-->

The following is a list of links for data providers and web applications developers that provide the means to create new deployments, upload conforming [DAC NetCDF files](ngdac-netcdf-file-format-version-2.html), view data set status and programmatically interface with the DAC via a RESTful API.

<!--
# Contents

- [Utilities and Resources for Data Providers](#utilities-and-resources-for-data-providers)
- [Links](#links)
- [Interacting with the DAC](#link-use-and-descriptions)
-->

## Utilities and Resources for Data Providers

The following is a list of useful scripts and utilities for registered and prospective data providers

 - [Simple DAC NetCDF File Validator](https://github.com/kerfoot/nc-validate)
  This python script compares a list of one or more NetCDF files to a known conforming [DAC NetCDF file](ngdac-netcdf-file-format-version-2.html) and prints the results to STDOUT and STDERR.  If your files validate against this script they will be accepted by the DAC.  It is <b>highly recommended</b> that you use this script to help you check your [DAC NetCDF files](ngdac-netcdf-file-format-version-2.html) before submitting them as it will significantly decrease your development time.  This script requires the following non-core modules:
    + [Python netcdf4](http://netcdf4-python.googlecode.com/svn/trunk/docs/netCDF4-module.html)
 - [FTP script](https://github.com/ioos/ioosngdac/blob/master/util/ncFtp2ngdac.pl) for automating uploads of [conforming](ngdac-netcdf-file-format-version-2.html) NetCDF files to the DAC ftp server.  The script is written in Perl and requires the following non-core modules:
    + [Readonly](http://search.cpan.org/~roode/Readonly-1.03/Readonly.pm)
    + [Net::FTP](http://search.cpan.org/~shay/libnet-1.25/Net/FTP.pm)

## Useful DAC Links

The following is a list of links that will take you directly to the specified resource.

## Submitting Data
 - [Deployment Registration](https://gliders.ioos.us/providers)
 - [NetCDF FTP server](ftp://data.ioos.us/)


## Data Access Links
Access to the datasets submitted to the DAC is provided via [ERDDAP](http://coastwatch.pfeg.noaa.gov/erddap/information.html) and [THREDDS](http://www.unidata.ucar.edu/software/thredds/current/tds/).  The access points are:

 - [**ERDDAP Dataset Access**](https://gliders.ioos.us/erddap/tabledap/index.html)
 - [**THREDDS Dataset Access**](https://gliders.ioos.us/thredds/catalog.html)

## Dataset Status

 - [**Dataset Status**](https://gliders.ioos.us/status)

## APIs

 - [**DAC RESTful API**](https://gliders.ioos.us/providers/api/deployment)


## IOOS Resources

The following is a list of links to [U.S. IOOS](https://ioos.us) projects related to the DAC:

 - [**IOOS Gliders and the DAC**](https://gliders.ioos.us/data)
 - [**IOOS GliderDAC Map**](https://gliders.ioos.us/map)
 - [**IOOS Catalog**](https://data.ioos.us/)


