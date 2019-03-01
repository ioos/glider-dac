---
title: Home
wikiPageName: Home
keywords: IOOS, documentation
tags: [getting_started, about, overview]
toc: false
#search: exclude
#permalink: index.html
summary: This wiki is a collection of documents and resources describing the NetCDF file specification, data provider registration and data set submission processes for contributing real-time and delayed-mode glider data sets to the U.S. IOOS National Glider Data Assembly Center (NGDAC).
---

<!--
This wiki is a collection of documents and resources describing the NetCDF file specification, data provider registration and data set submission processes for contributing real-time and delayed-mode glider data sets to the U.S. IOOS <b>N</b>ational <b>G</b>lider <b>D</b>ata <b>A</b>ssembly <b>C</b>enter (__NGDAC__).

## Wiki Contents

+ [Introduction](#introduction)
+ [Glider Background and Sampling Terminology](https://github.com/kerfoot/ioosngdac/wiki/Glider-Background-and-Sampling-Terminology)
+ [NetCDF file format description](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2)
+ [Links for Data Providers](https://github.com/ioos/ioosngdac/wiki/Links-for-Data-Providers)
+ [NGDAC Architecture](https://github.com/kerfoot/ioosngdac/wiki/NGDAC-Architecture)
+ [NGDAC NetCDF File Submission Process](https://github.com/kerfoot/ioosngdac/wiki/NGDAC-NetCDF-File-Submission-Process)
+ [Backup and Recovery](https://github.com/ioos/ioosngdac/wiki/Data-Backup-Recovery)
-->

## Introduction

The goals of the <b>U.S. IOOS National Glider Data Assembly Center</b>:

 + Develop a simple, fully self-describing [NetCDF](http://en.wikipedia.org/wiki/NetCDF) file specification that preserves the resolution of the original glider data sets.
 + Provide glider operators with a simple process for registering and submitting glider data sets to a centralized storage location.
 + Provide public access to glider data sets via existing web services and standards, in a variety of well-known formats.
 + Facilitate the distribution of glider data sets on the [Global Telecommunication System](http://www.wmo.int/pages/prog/www/TEM/GTS/index_en.html).
 + Work with the [National Ocean Data Center](http://www.nodc.noaa.gov/index.html) to create a permanent data archive.

The **NGDAC** accepts a [simple NetCDF file](https://github.com/kerfoot/ioosngdac/wiki/NetCDF-File-Format-Description) containing water column measurements collected by a glider during a single profile.  Groups of these NetCDF files, gathered during a deployment (also known as a **trajectory**), are uploaded to the **NGDAC** by individual glider operators.  Once they arrive at the **NGDAC**, the files are validated for compliance, aggregated into a single dataset representing the **deployment/trajectory** and distributed via [ERDDAP](http://coastwatch.pfeg.noaa.gov/erddap/information.html) and [THREDDS](http://www.unidata.ucar.edu/software/thredds/current/tds/TDS.html) end-points.  The data sets served by the **NGDAC** provide access to the **trajectory/deployment** data both as time-series and on a profile-by-profile basis.

Transmission of the data sets via the [Global Telecommunication System](http://www.wmo.int/pages/prog/www/TEM/GTS/index_en.html) is made possible by the [National Data Buoy Center](http://www.ndbc.noaa.gov/), which accesses the data sets from the **ERDDAP** and/or **THREDDS** end-points. After performing some internal quality checks, the profiles are encoded into [BUFR](http://en.wikipedia.org/wiki/BUFR) format and released on the [Global Telecommunication System](http://www.wmo.int/pages/prog/www/TEM/GTS/index_en.html), making them available for assimilation by regional and global scale ocean forecasting models.

Please read the documentation **thoroughly** before beginning the data submission process.  Additional questions and information requests should be directed to:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`   ioos.glider.data@noaa.gov`

