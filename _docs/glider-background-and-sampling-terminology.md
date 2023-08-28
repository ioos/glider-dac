---
title: Glider Background and Sampling Terminology
wikiPageName: Glider-Background-and-Sampling-Terminology
keywords: IOOS, documentation
tags: [getting_started, about, overview]
toc: false
#search: exclude
#permalink: index.html
summary: This page defines glider and sampling terminology used throughout the rest of the Wiki.
---
<!--
> [Wiki](https://github.com/kerfoot/glider-dac/wiki) ▸ **Glider Background and Sampling Terminology**

## Contents

+ [Glider Types](#glider-types)
+ [Sampling Pattern Terminology](#sampling-pattern-terminology)
+ [NetCDF File Format Description](ngdac-netcdf-file-format-version-2.html)
-->

## Glider Types
As of this writing, there are 3 major buoyancy driven glider types that are currently utilized by IOOS Regional Associations:
 + [Seaglider](https://apl.uw.edu/project/project.php?id=seaglider): originally designed and built through a collaboration with the University of Washington's [Applied Physics Lab](https://apl.uw.edu/) and [School of Oceanography](https://www.ocean.washington.edu/).
 + [Spray](https://spray.ucsd.edu/pub/rel/info/spray_description.php): originally designed by [Scripps Institution of Oceanography](https://scripps.ucsd.edu/) and [Woods Hole Oceanographic Institution](http://www.whoi.edu/) with funding provided by the [Office of Naval Research](https://www.nre.navy.mil/), the Spray glider is now manufactured by [Bluefin Robotics](https://gdmissionsystems.com/underwater-vehicles/bluefin-robotics/).
 + [Slocum](https://www.teledynemarine.com/en-us/products/product-line/Pages/Autonomous-Underwater-Glider.aspx): designed and built by [Teledyne Webb Research Corporation](https://www.teledynemarine.com/brands/webb-research/).

## Sampling Pattern Terminology

The schematic and definitions below define the sampling terminology of a profiling glider.  While all of the terms defined below are commonly used in the glider community, the 2 fundamental terms used by the **NGDAC** to organize data are the **profile** and **trajectory**.  The **NGDAC** receives glider data as individual, sequentially numbered **profiles** and aggregates files from the same **trajectory** into a single data set representing the deployment.

![Glider Sampling Patterns and Terms](/glider-dac/glider-sampling-terminology.png)

 + **Profile**: A single vertically oriented track of a glider, either upward or downward through the water column.  A profile is one-half of a **dive**.  The profile is the fundamental atomic data type used by the **NGDAC**.  All data submitted to the **NGDAC** is submitted as individual profiles, containing the various water column properties or sensor values.  Examples of the file format description can be found as [CDL](https://github.com/kerfoot/glider-dac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.cdl), [NetCDF file](https://github.com/kerfoot/glider-dac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.nc) and [ncml](https://github.com/kerfoot/glider-dac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.ncml) can be found [here](https://github.com/kerfoot/glider-dac/tree/master/nc/template).
 + **Dive**: A single vertical <strong>profile</strong> to depth followed by a vertical **profile** towards the surface.  A dive does not necessarily begin with or terminate with a surfacing and/or gps fix.
 + **Segment**: The set of data collected between 2 gps fixes obtained while the glider is on the surface of the water.  The first gps fix is acquired prior to the beginning of a dive and the second gps fix is acquired following the completion of at least one dive.  Glider **segments** always consist of at least one, and possibly many **dives**.
 + **Trajectory** or **Deployment**: A series of one or more **segments** completed by a glider between the time of deployment and the time of recovery.

A detailed description of the official NetCDF file format used by the **NGDAC** can be found [here](ngdac-netcdf-file-format-version-2.html).
