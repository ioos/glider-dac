---
title: Overview
wikiPageName: Home
keywords: IOOS, documentation
tags: [getting_started, about, overview]
toc: false
#search: exclude
#permalink: index.html
summary: This wiki is a collection of documents and resources describing the NetCDF file specification, data provider registration and data set submission processes for contributing real-time and delayed-mode glider data sets to the U.S. IOOS National Glider Data Assembly Center (NGDAC).
---

## Introduction

The goals of the <b>U.S. IOOS National Glider Data Assembly Center</b>:

 + Develop a simple, fully self-describing [NetCDF](https://docs.unidata.ucar.edu/netcdf-c/current/) file specification that preserves the resolution of the original glider data sets.
 + Provide glider operators with a simple process for registering and submitting glider data sets to a centralized storage location.
 + Provide public access to glider data sets via existing web services and standards, in a variety of well-known formats.
 + Facilitate the distribution of glider data sets on the [Global Telecommunication System](https://community.wmo.int/en/activity-areas/global-telecommunication-system-gts).
 + Work with the [National Centers for Environmental Information](https://www.ncei.noaa.gov/) to create a permanent data archive.

The **NGDAC** accepts a [simple NetCDF file](ngdac-netcdf-file-format-version-2) containing water column measurements collected by a glider during a single profile (see glider sampling terminology [here](glider-background-and-sampling-terminology#sampling-pattern-terminology)).  Groups of these NetCDF files, gathered during a deployment (also known as a [**trajectory**](glider-background-and-sampling-terminology#sampling-pattern-terminology)), are uploaded to the **NGDAC** by individual glider operators.  Once they arrive at the **NGDAC**, the files are validated for compliance, aggregated into a single dataset representing the **deployment/trajectory** and distributed via [ERDDAP](https://coastwatch.pfeg.noaa.gov/erddap/information.html) and [THREDDS](https://www.unidata.ucar.edu/software/tds/) end-points.  The data sets served by the **NGDAC** provide access to the **trajectory/deployment** data both as time-series and on a profile-by-profile basis.

Transmission of the data sets via the [Global Telecommunication System](https://community.wmo.int/en/activity-areas/global-telecommunication-system-gts) is made possible by the [National Data Buoy Center](http://www.ndbc.noaa.gov/), which accesses the data sets from the **ERDDAP** and/or **THREDDS** end-points. After performing some internal quality checks, the profiles are encoded into [BUFR](http://en.wikipedia.org/wiki/BUFR) format and released on the [Global Telecommunication System](https://community.wmo.int/en/activity-areas/global-telecommunication-system-gts), making them available for assimilation by regional and global scale ocean forecasting models.

Additional questions and information requests should be directed to:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[glider.dac.support@noaa.gov](mailto:glider.dac.support@noaa.gov?subject=GliderDAC%20Support)
