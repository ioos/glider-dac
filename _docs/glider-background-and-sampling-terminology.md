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
> [Wiki](https://github.com/kerfoot/ioosngdac/wiki) ▸ **Glider Background and Sampling Terminology**

## Contents

+ [Glider Types](#glider-types)
+ [Sampling Pattern Terminology](#sampling-pattern-terminology)
+ [NetCDF File Format Description](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2)
-->

## Glider Types
As of this writing, there are 3 major buoyancy driven glider types that are currently utilized by IOOS Regional Associations:
 + [Seaglider](http://www.apl.washington.edu/projects/seaglider/summary.html): originally designed and built through a collaboration with the University of Washington's [Applied Physics Lab](http://www.apl.washington.edu/) and [School of Oceanography](http://www.ocean.washington.edu/).  The Seaglider is now manufactured by [Kongsberg Maritime](http://www.km.kongsberg.com/ks/web/nokbg0240.nsf/AllWeb/EC2FF8B58CA491A4C1257B870048C78C?OpenDocument).
 + [Spray](http://spray.ucsd.edu/pub/rel/info/spray_description.php): originally designed by [Scripps Institution of Oceanography](https://scripps.ucsd.edu/) and [Woods Hole Oceangraphic Institution](http://www.whoi.edu/) with funding provided by the [Office of Naval Research](http://www.onr.navy.mil/), the Spray glider is now manufactured by [Bluefin Robotics](http://www.bluefinrobotics.com/products/spray-glider/).
 + [Slocum](http://www.webbresearch.com/slocumglider.aspx): designed and built by [Teledyne Webb Research Corporation](http://www.webbresearch.com/).

## Sampling Pattern Terminology

The schematic and definitions below define the sampling terminology of a profiling glider.  While all of the terms defined below are commonly used in the glider community, the 2 fundamental terms used by the **NGDAC** to organize data are the **profile** and **trajectory**.  The **NGDAC** receives glider data as individual, sequentially numbered **profiles** and aggregates files from the same **trajectory** into a single data set representing the deployment.

<!-- ![Glider Sampling Patterns and Terms](https://raw.githubusercontent.com/kerfoot/ioosngdac/master/doco/glider-sampling-terminology.png) -->
![Glider Sampling Patterns and Terms](/ioosngdac/glider-sampling-terminology.png)

 + **Profile**: A single vertically oriented track of a glider, either upward or downward through the water column.  A profile is one-half of a **dive**.  The profile is the fundamental atomic data type used by the **NGDAC**.  All data submitted to the **NGDAC** is submitted as individual profiles, containing the various water column properties or sensor values.  Examples of the file format description can be found as [CDL](https://github.com/kerfoot/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.cdl), [NetCDF file](https://github.com/kerfoot/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.nc) and [ncml](https://github.com/kerfoot/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.ncml) can be found [here](https://github.com/kerfoot/ioosngdac/tree/master/nc/template).
 + **Dive**: A single vertical <strong>profile</strong> to depth followed by a vertical **profile** towards the surface.  A dive does not necessarily begin with or terminate with a surfacing and/or gps fix.
 + **Segment**: The set of data collected between 2 gps fixes obtained while the glider is on the surface of the water.  The first gps fix is acquired prior to the beginning of a dive and the second gps fix is acquired following the completion of at least one dive.  Glider **segments** always consist of at least one, and possibly many **dives**.
 + **Trajectory** or **Deployment**: A series of one or more **segments** completed by a glider between the time of deployment and the time of recovery.

A detailed description of the official NetCDF file format used by the **NGDAC** can be found [here](NGDAC-NetCDF-File-Format-Version-2).
