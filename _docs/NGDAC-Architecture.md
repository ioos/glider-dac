> [Wiki](https://github.com/kerfoot/ioosngdac/wiki) ▸ **NGDAC Architecture**

This page presents an in-depth description and discussion of the <b>U.S. IOOS National Data Assembly Center</b> architecture.

# Contents

+ [Data Assembly Center Architecture](#data-assembly-center-architecture)
+ [Data Provider Responsibilities](#data-provider-responsibilities)
+ [NGDAC Responsibilities](#ngdac-responsibilities)

## Data Assembly Center Architecture

The following diagram illustrates the architecture of the <b>U.S. IOOS National Glider Data Assembly Center</b> and end-to-end data flow pathway. 

![NGDAC Architecture](https://raw.githubusercontent.com/kerfoot/ioosngdac/master/doco/IOOS-DAC-architecture.png)

## Data Provider Responsibilities

The primary role of the individual glider operators is to write and submit [compliant]() NetCDF data files to the <b>U.S. IOOS National Glider Data Assembly Center's</b> ftp site.  All subsequent archiving and data product generation is done by the <b>NGDAC</b>.  Specifically, individual glider operators/data providers are responsible for the following:

1. Register as a data provider by providing a point of contact for the institution submitting data files.
2. Request a WMO ID from the <b>NGDAC</b>.
3. Initialize a new deployment at the <a href="http://gliders.ioos.us"><b>NGDAC</b></a> website by completing a simple form describing the deployment.
4. Ftp new NetCDF files to the <b>NGDAC</b> as they become available.

A [detailed description](https://github.com/kerfoot/ioosngdac/wiki/NGDAC-NetCDF-File-Submission-Process) of these steps can be found on the [wiki](https://github.com/kerfoot/ioosngdac/wiki).

## NGDAC Responsibilities
