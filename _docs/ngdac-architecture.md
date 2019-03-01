---
title: NGDAC Architecture
wikiPageName: NGDAC-Architecture
keywords: IOOS, documentation
tags: [getting_started, about, overview]
toc: false
#search: exclude
#permalink: index.html
summary: This page presents an in-depth description and discussion of the U.S. IOOS National Data Assembly Center architecture.
---

<!--
> [Wiki](https://github.com/kerfoot/ioosngdac/wiki) ▸ **NGDAC Architecture**

# Contents

+ [Data Assembly Center Architecture](#data-assembly-center-architecture)
+ [Data Provider Responsibilities](#data-provider-responsibilities)
+ [NGDAC Responsibilities](#ngdac-responsibilities)
-->

## Data Assembly Center Architecture

The following diagram illustrates the architecture of the <b>U.S. IOOS National Glider Data Assembly Center</b> and end-to-end data flow pathway.

<!-- ![NGDAC Architecture](https://raw.githubusercontent.com/kerfoot/ioosngdac/master/doco/IOOS-DAC-architecture.png) -->
![NGDAC Architecture](/ioosngdac/IOOS-DAC-architecture.png)

## Data Provider Responsibilities

The primary role of the individual glider operators is to write and submit [compliant]() NetCDF data files to the <b>U.S. IOOS National Glider Data Assembly Center's</b> ftp site.  All subsequent archiving and data product generation is done by the <b>NGDAC</b>.  Specifically, individual glider operators/data providers are responsible for the following:

 1. Register as a data provider by providing a point of contact for the institution submitting data files.
 2. Request a WMO ID from the **NGDAC**.
 3. Initialize a new deployment at the [**NGDAC**](http://gliders.ioos.us) website by completing a simple form describing the deployment.
 4. Ftp new NetCDF files to the **NGDAC** as they become available.

A [detailed description](/ioosngdac/NGDAC-NetCDF-File-Submission-Process) of these steps can be also found on the [NGDAC GitHub repo Wiki](https://github.com/kerfoot/ioosngdac/wiki).

## NGDAC Responsibilities

Coming soon...
