---
title: NGDAC NetCDF File Format Version 2
wikiPageName: NGDAC-NetCDF-File-Format-Version-2
keywords: IOOS, documentation
tags: [getting_started, about, overview]
toc: false
#search: exclude
#permalink: index.html
summary: A description of the NetCDF file format specification
---

<!--

> [Wiki](https://github.com/ioos/ioosngdac/wiki) ▸ **NetCDF File Format Description**

# Contents
 + [Introduction](#introduction)
 + [File Naming Conventions](#file-naming-conventions)
 + [Global Attributes](#global-attributes)
 + [Variables](#variables)
   - [trajectory](#trajectory)
   - [time](#time)
   - [time_qc](#time_qc)
   - [lat](#lat)
   - [lat_qc](#lat_qc)
   - [lon](#lon)
   - [lon_qc](#lon_qc)
   - [pressure](#pressure)
   - [pressure_qc](#pressure_qc)
   - [depth](#depth)
   - [depth_qc](#depth_qc)
   - [temperature](#temperature)
   - [temperature_qc](#temperature_qc)
   - [conductivity](#conductivity)
   - [conductivity_qc](#conductivity_qc)
   - [density](#density)
   - [density_qc](#density_qc)
   - [profile_id](#profile_id)
   - [profile_time](#profile_time)
   - [profile_time_qc](#profile_time_qc)
   - [profile_lat](#profile_lat)
   - [profile_lat_qc](#profile_lat_qc)
   - [profile_lon](#profile_lon)
   - [profile_lon_qc](#profile_lon_qc)
   - [salinity](#salinity)
   - [salinity_qc](#salinity_qc)
   - [time_uv](#time_uv)
   - [time_uv_qc](#time_uv_qc)
   - [lat_uv](#lat_uv)
   - [lat_uv_qc](#lat_uv_qc)
   - [lon_uv](#lon_uv)
   - [lon_uv_qc](#lon_uv_qc)
   - [u](#u)
   - [u_qc](#u_qc)
   - [v](#v)
   - [v_qc](#v_qc)
   - [platform](#platform)
   - [instrument_ctd](#instrument_ctd)

-->

## Introduction

This page provides an in-depth description of the NetCDF file format specification (**IOOS_Glider_NetCDF_v2.0.nc**) used by the **U.S. IOOS National Glider Data Assembly Center** to archive and distribute real-time and delayed-mode glider data sets. A thorough reading is **strongly** recommended prior to beginning the [submission](/ioosngdac/ngdac-netcdf-file-submission-process.html) process.

**Examples** of the file specification are available as [**NetCDF**](https://github.com/ioos/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.nc), [**CDL**](https://github.com/ioos/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.cdl), and [**ncml**](https://github.com/ioos/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.ncml) are available [here](https://github.com/ioos/ioosngdac/tree/master/nc/template).

The NetCDF file specification detailed below serves 2 primary purposes:
 + Provide a complete metadata record for all glider data submitted to the **NGDAC** that can be harvested and stored by existing catalogs and registries.
 + Provide a simple file format that is easily created by glider operators and data managers. The flexibility provided by this specification allows for the creation of compound data products that result in easier, more intuitive methods of access by a wide range of end-users and in a variety of formats (i.e.: [**csv**](http://en.wikipedia.org/wiki/Comma-separated_values), [**tsv**](http://en.wikipedia.org/wiki/Tab-separated_values), [**json**](http://en.wikipedia.org/wiki/JSON), [**geoJson**](http://en.wikipedia.org/wiki/GeoJSON), etc.).
 + Preserve the original resolution of the data sets.

Once the files have been uploaded by the individual glider operators, they are aggregated into a single data set (via [**ERDDAP**](http://coastwatch.pfeg.noaa.gov/erddap/information.html)) representing the entire **deployment/trajectory**. These **deployment/trajectory** datasets are publicly accessible via [**ERDDAP**](http://coastwatch.pfeg.noaa.gov/erddap/information.html) and [**THREDDS**](http://www.unidata.ucar.edu/software/thredds/current/tds/TDS.html) end-points. The files submitted by glider operators are archived by the **NGDAC**, but are **not** available for public access in their original form. The **NGDAC** uses a private [**ERDDAP**](http://coastwatch.pfeg.noaa.gov/erddap/information.html) server to aggregate the individual files into a single file representing the **trajectory**, in which all original metadata and sampling resolution is preserved.

## File Naming Conventions

The following list specifies the 2 file types which will be accepted by the **U.S IOOS National Glider Data Assembly Center** and the required naming conventions for each:

 - **glider_yyyymmddTHHMMSSZ_rt.nc:** Data gathered in real-time or near real-time. These files typically contain a subset of the full-resolution data provided in the delayed mode NetCDF files.
 - **glider_yyyymmddTHHMMSSZ_delayed.nc:** Delayed-mode data set typically submitted after the glider is recovered. **Delayed mode data may include a quality assessment but this is not required currently.**

Where

_glider_
: Identifying name or type abbreviation for the glider

_yyyymmddTHHMMSSZ_
: [ISO 8601](http://en.wikipedia.org/wiki/ISO_8601) formatted date representing the start time of the data acquisition, followed by **Z** to denote UTC time, not a local time zone.

_'rt' or 'delayed'_
: string specifying real-time (during deployment) or delayed mode (post-recovery) data acquisition

Ideally, the <strong>glider_yyyymmddTHHMMSS_rt.nc</strong> files will be provided by the individual operators during the deployment and the <strong>glider_yyyymmddTHHMMSS_delayed.nc</strong> files will be provided after the glider has been recovered and the full data set processed. It is expected, where applicable, that all files will contain the appropriate <strong>VARIABLE_qc</strong> variables to convey some level of quality assurance for the data. A discussion of these variables and their relationship to the sensor variables is found [below](#variables).

## Global Attributes

The following is the list of required global attributes that must be included in each NetCDF file submitted to the **NGDAC**. This list was created from a variety of sources with the goal of providing a complete metadata record of the data set. More information on these sources can be found at the following locations:
 - **CF1.6**: Section 2.6 of the current (v1.6) Climate and Forecast [conventions](http://cf-pcmdi.llnl.gov/documents/cf-conventions/1.6/cf-conventions.html#description-of-file-contents)
 - **ACDD**: Attribute Conventions for Dataset Discovery [Home page](http://wiki.esipfed.org/index.php?title=Category:Attribute_Conventions_Dataset_Discovery) and [Current Standard](http://wiki.esipfed.org/index.php/Attribute_Convention_for_Data_Discovery_%28ACDD%29)
 - **NCEI**: Guidance from NOAA's National Centers for Environmental Information on netCDF templates to promote good stewardship and archiving. [NCEI Templates](https://www.nodc.noaa.gov/data/formats/netcdf/) and [global attribute suggestions](https://www.nodc.noaa.gov/data/formats/netcdf/#guidancetable).
 - **IMOS/ANFOG**: IMOS Data Management manual version [3.1](http://imos.org.au/fileadmin/user_upload/shared/ANFOG/ANFOG_data_management3_1.pdf)
 - **IOOS**: Internal discussion within the IOOS Glider Data Team.

### Caveats

There are a few **important** points to mention with regards to global attributes:

 1. All attributes listed below are **REQUIRED** and should have meaningful values assigned to them. In the event that a meaningful value cannot be assigned, set the value to a single whitespace character enclosed in double quotes. For example, if the data set has not been modified, you should set the **date_modified** attribute value to **\" \"**.
 2. For attributes with timestamp values (i.e.: **date_created**, **date_modified**, **date_issued**), use the [ISO 8601:2004 'extended' format](http://en.wikipedia.org/wiki/ISO_8601#General_principles). This format has the general form: **YYYY-MM-DDThh:mm:ssZ**.
 3. All global attributes must be string attributes.
 4. You may or may not notice the absence of a number of global attributes, particularly related to temporal and spatial extent (i.e.: **geospatial_lat_min**, **geospatial_vertical_min**, **time_coverage_start**, etc.), from this list. The **NGDAC** will add these global attributes and assign appropriate values to them prior to making the aggregated data sets available to the public.
 5. The name and a description of each attribute are listed below. An example is given where the selection of an appropriate value may be unclear. Please use the specified **Value** listed under the attribute name for the following attributes: **Conventions**, **Metadata_Conventions**, **format_version**, **standard_name_vocabulary**.

### Description & Examples of Required Global Attributes

#### _Conventions_

Version of the [Climate and Forecast metadata conventions](http://cfconventions.org/) followed by the file format specification.

Value:
: "CF-1.6"

#### _Metadata_Conventions_

Unidata NetCDF group's [Attribute Conventions for Dataset Discovery](http://wiki.esipfed.org/index.php?title=Category:Attribute_Conventions_Dataset_Discovery). These conventions identify and define a list of NetCDF global attributes recommended for describing a NetCDF dataset to discovery systems such as Digital Libraries. Software tools will use these attributes for extracting metadata from datasets, and exporting to Dublin Core, DIF, ADN, FGDC, ISO 19115 etc. metadata formats.

Value:
: "CF-1.6, Unidata Dataset Discovery v1.0"

#### _acknowledgement_

String used to properly acknowledge use of the data.

Example:
: "This work supported by funding from NOAA"

#### _comment_

Free-form field used to provide additional information on the data set

#### _contributor_name_

A comma separated list of contributors to this data set.

Example:
: "Jerry Garcia, Bob Weir, Bill Graham"

#### _contributor_role_

A comma separated list of the roles of those specified using the **contributor_name** attribute.

Example:
: "Principal Investigator, Principal Investigator, Data Manager"

#### _creator_email_

Email address for person who collected the data.

#### _creator_name_

Name of the person who collected the data.

#### _creator_url_

URL for person who collected the data.

#### _date_created_

Creation date of the file. Use the [ISO 8601:2004](http://en.wikipedia.org/wiki/ISO_8601) Extended Date/Time format.

Example:
: "1977-05-08T20:00:00Z"

#### _date_issued_

The date on which this data was formally issued. Use the [ISO 8601:2004](http://en.wikipedia.org/wiki/ISO_8601) Extended Date/Time format.

Example:
: "1992-06-25T20:00:00Z"

#### _date_modified_

Modification date of the file, if any. Use the [ISO 8601:2004](http://en.wikipedia.org/wiki/ISO_8601) Extended Date/Time format.

Example:
: "1978-06-04T20:00:00Z"

#### _format_version_

NetCDF file format version.

Value:
: "IOOS_Glider_NetCDF_v2.0.nc"

#### _history_

This is String with one or more lines, each of which has the [ISO 8601:2004](http://en.wikipedia.org/wiki/ISO_8601) Extended Date/Time Format (EDTF) and the name and command line parameters of the program used to create or change the data and/or other information about the change.

Example:
: "2014-07-21T00:00:00Z: /bin/writeIoosNc.py"

#### _id_

A human readable unique identifier for data set. We recommend using the **trajectory** variable string name, which must have the following format:

  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;_**glider-YYYYmmddTHHMM**_

Where **`glider`** is the name of the glider and **`YYYYmmddTHHMM`** is the deployment date/time.

Example:
: "ru30-20140101T0000"

#### _institution_

Institution of the person or group that collected the data. This value should be identical to the "Operator" specified on the [https://gliders.ioos.us](https://gliders.ioos.us) deployment page.

Example:
: "Rutgers University"

#### _keywords_

A comma separated list of keywords coming from the **keywords_vocabulary</b>.

Example:
: "AUVS > Autonomous Underwater Vehicles, Oceans > Ocean Pressure > Water Pressure, Oceans > Ocean Temperature > Water Temperature, Oceans > Salinity/Density > Conductivity, Oceans > Salinity/Density > Density, Oceans > Salinity/Density > Salinity"

#### _keywords_vocabulary_

Identifies the controlled keyword vocabulary used to specify the values within the **keywords** attribute.

Example:
: "GCMD Science Keywords"

#### _license_

Describe the restrictions to data access and distribution.

Example:
: "This data may be redistributed and used without restriction."

#### _metadata_link_

This attribute provides a link to a complete metadata record for this data set or the collection that contains this data set.

#### _naming_authority_

Backward URL of institution.

Example:
: "edu.rutgers.marine.rucool"

#### _platform_type_

Glider type.

Current accepted types are:

: "Seaglider", "Spray", "Slocum"

No other values will be accepted for this attribute.

#### _processing_level_

Provide a description of the processing or quality control level of the data.

Example:
: "Data provided as is with no expressed or implied assurance of quality assurance or quality control."

#### _project_

Project the data was collected under.

Example:
: "TEMPESTS"

#### _publisher_email_

Email address of the publisher of the data.

#### _publisher_name_

Name of the publisher of the data.

#### _publisher_url_

A URL for the publisher of the data.

#### _references_

Published or web-based references that describe the data or methods used to produce it.

#### _sea_name_

The names of the sea in which the data were collected. Use NODC sea names table. Currently located at: [http://www.nodc.noaa.gov/General/NODC-Archive/seanamelist.txt](http://www.nodc.noaa.gov/General/NODC-Archive/seanamelist.txt).

#### _source_

The input data sources regardless of the method of production method used.

Example:
: "Observational data from a profiling glider."

#### _standard_name_vocabulary_

Version of CF standard names used for variables. [Current standard name table](http://cfconventions.org/standard-names.html) (e.g. "Standard Name Table (v48, 28 November 2017)")

#### _summary_

Provide a useful summary or abstract for the data in the file. This summary is used as the primary piece of information describing the data set for discovery and archiving purposes. As such, careful thought should be put into constructing the summary.

Example:
: "Slocum glider dataset gathered as part of the **TEMPESTS** (**T**he **E**xperiment to **M**easure and **P**redict **E**ast coast **ST**orm **S**trength), funded by NOAA through **CINAR** (**C**ooperative **I**nstitute for the **N**orth **A**tlantic **R**egion). This dataset contains physical oceanographic measurements of temperature, conductivity, salinity, density and estimates of depth-average currents."

  Regardless of the summary added by the data provider, the following summary is added to this attribute prior to archiving by NCEI:

  "**Addendum**: The Integrated Ocean Observing System's National Glider Data Assembly Center receives sets of individual NetCDF files comprising an individual glider deployment from data operators and providers around the world. These files are checked for compliance and then aggregated into a single data set representing the entire deployment and made available via ERRDAP and THREDDS end points, making the data sets available to the public. Currently, the data sets provide measurements of physical oceanographic properties (temperature, salinity, conductivity and density). Future plans, currently under development, include providing access to biological and chemical properties. Once the deployment has been completed, as specified by the glider operator or data provider, the data set is marked for archiving, at which point it is added to the National Centers for Environmental Information (NCEI, formerly NODC) data archive to create a permanent archive of the data set."


#### _title_

We recommend using the **trajectory** variable string name, which must have the following format:

   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **`glider-YYYYmmddTHHMM`**

Where **`glider`** is the name of the glider and **`YYYYmmddTHHMM`** is the deployment date/time.

Example:
: "ru30-20140101T0000"

#### _wmo_id_

String specifying the [WMO ID](http://www.wmo.int/pages/prog/amp/mmop/wmo-number-rules.html) used to identify this platform. Must be specified as a string attribute. Each [WMO ID](http://www.wmo.int/pages/prog/amp/mmop/wmo-number-rules.html) is unique to an individual glider deployed in a specific location and must be requested from the **NGDAC** administrator.

Example:
: "4801518"


## Variables

The NetCDF file specification contains 3 core variable types which relate to how the individual NetCDF files are aggregated by the **NGDAC**:

 + [time-series](#time-series-variables): dimensioned along the time axis to provide access to the data as time-series.
 + [profile](#dimensionless-profile-variables): dimensionless variables that provide access to data on a profile-by-profile basis
 + [container](#dimensionless-container-variables): dimensionless variables used to capture meta data regarding the platform and instrumentation on board the glider.

Most of the **time-series** variables and many of the **profile** variables have corresponding data quality variables, which are referenced via the **ancillary_variables** variable attribute. The dimensions of these variables are the same as the variables they convey quality information about.

While no CF standard names exist for these flags, CF conventions allow the use of a [standard_name modifier](http://cfconventions.org/Data/cf-convetions/cf-conventions-1.7/build/cf-conventions.html#standard-name-modifiers) to be appended to the corresponding variable's standard name to create the standard name for the quality control flag. For example, the **temperature** variable has a corresponding data quality variable (**temperature_qc**). The **standard_name** attribute contains the CF standard name of the variable it references with **status_flag** appeneded, i.e.: **temperature** **status_flag**

The following is a list and description of all variables and corresponding variable attributes that are **REQUIRED** for the file to be accepted by the **NGDAC**. An CDL description of each variable is located below the formal description. Examples of the various attributes have been provided for reference, but each data provider is encouraged to modify these values if they feel it is necessary, particularly for the following attributes:

 + **comment**
 + **valid_min**
 + **valid_max**
 + **accuracy**
 + **precision**
 + **resolution**
 + **platform:wmo_id**
 + **platform:id**
 + **platform:long_name**
 + All **instrument_ctd** attributes except **instrument_ctd:platform**

**Examples** of the file specification are available as [**NetCDF**](https://github.com/ioos/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.nc), [**CDL**](https://github.com/ioos/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.cdl), and [**ncml**](https://github.com/ioos/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.ncml) are available [**here**](https://github.com/ioos/ioosngdac/tree/master/nc/template).

### Dimensions

NetCDF files submitted by the individual glider operators contain 2 dimension variables:

 + **time**: time when the individual sensor record was recorded.
 + **traj_strlen**: string specifying the trajectory name.

According to [CF Conventions](http://cfconventions.org/Data/cf-convetions/cf-conventions-1.7/build/cf-conventions.html#idm43169986560), dimension variables are not allowed to have missing values (i.e.: _FillValue).

The aggregated data sets created by the **NGDAC** contain the following additional dimensions to increase the data access methods and are **NOT** included in the individual profile NetCDF files submitted by the glider operators:

 + **trajectory**
 + **profile**
 + **obs**
 + **wmo_id_strlen**

### Trajectory Variables

The **trajectory** variable stores a character array that identifies the deployment during which the data was gathered. This variable is used by the DAC to aggregate all individual NetCDF profiles containing the same trajectory value into a single trajectory profile data set. This value should be a character array that uniquely identifies the deployment. Each individual NetCDF file from the deployment data set must have the same value.

#### _trajectory_

|&nbsp;|&nbsp;|
|-|-|
| **Dimension** | traj_strlen |
| **Data Type** | string stored as char array |
| **Value Type** | array |
| **_FillValue** | "" |
| **Description** | String representation of the trajectory specified using the format: **GLIDER-YYYYmmddTHHMM</b>. |



[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 char trajectory(traj_strlen) ;
        trajectory:cf_role = "trajectory_id" ;
        trajectory:comment = "A trajectory is a single deployment of a glider and may span multiple data files." ;
        trajectory:long_name = "Trajectory/Deployment Name" ;
```


### Time-Series Variables

The following variables are dimensioned along the time axis.

#### <i>time</i>

**IMPORTANT: The CF specification does not allow coordinate variables to contain missing/_FillValue values.</b>


| | |
|-|-|
| **Dimension** | time |
| **Data Type** | double |
| **Value Type** | array |
| **Description** | An array containing the time stamp corresponding to the acquisition of the sensor data for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double time(time) ;
        time:ancillary_variables = "time_qc" ;
        time:calendar = "gregorian" ;
        time:long_name = "Time" ;
        time:observation_type = "measured" ;
        time:standard_name = "time" ;
        time:units = "seconds since 1970-01-01T00:00:00Z" ;
```


#### <i>time_qc</i>



| | |
|-|-|
| **Dimension** | time |
| **Data Type** | byte |
| **Value Type** | array |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the values in the **time** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte time_qc(time) ;
        time_qc:_FillValue = -127b ;
        time_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        time_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        time_qc:long_name = "time Quality Flag" ;
        time_qc:standard_name = "time status_flag" ;
        time_qc:valid_max = 9b ;
        time_qc:valid_min = 0b ;

```

#### <i>lat</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | double |
| **Value Type** | array |
| **_FillValue** | -999. |
| **Description** | An array containing the time-series of measured and/or interpolated latitudes for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double lat(time) ;
        lat:_FillValue = -999. ;
        lat:ancillary_variables = "lat_qc" ;
        lat:comment = "Values may be interpolated between measured GPS fixes" ;
        lat:coordinate_reference_frame = "urn:ogc:crs:EPSG::4326" ;
        lat:long_name = "Latitude" ;
        lat:observation_type = "measured" ;
        lat:platform = "platform" ;
        lat:reference = "WGS84" ;
        lat:standard_name = "latitude" ;
        lat:units = "degrees_north" ;
        lat:valid_max = 90. ;
        lat:valid_min = -90. ;
```


#### <i>lat_qc</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | byte |
| **Value Type** | array |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the values in the **lat** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte latitude_qc(time) ;
        lat_qc:_FillValue = -127b ;
        lat_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        lat_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        lat_qc:long_name = "latitude Quality Flag" ;
        lat_qc:standard_name = "latitude status_flag" ;
        lat_qc:valid_max = 9b ;
        lat_qc:valid_min = 0b ;
```


#### <i>lon</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | double |
| **Value Type** | array |
| **_FillValue** | -999. |
| **Description** | An array containing the time-series of measured and/or interpolated longitudes for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double lon(time) ;
        lon:_FillValue = -999. ;
        lon:ancillary_variables = "lon_qc" ;
        lon:comment = "Values may be interpolated between measured GPS fixes" ;
        lon:coordinate_reference_frame = "urn:ogc:crs:EPSG::4326" ;
        lon:long_name = "Longitude" ;
        lon:observation_type = "measured" ;
        lon:platform = "platform" ;
        lon:reference = "WGS84" ;
        lon:standard_name = "longitude" ;
        lon:units = "degrees_east" ;
        lon:valid_max = 180. ;
        lon:valid_min = -180. ;
```


#### <i>lon_qc</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | byte |
| **Value Type** | array |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the values in the **lon** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte lon_qc(time) ;
        lon_qc:_FillValue = -127b ;
        lon_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        lon_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        lon_qc:long_name = "longitude Quality Flag" ;
        lon_qc:standard_name = "longitude status_flag" ;
        lon_qc:valid_max = 9b ;
        lon_qc:valid_min = 0b ;
```


#### <i>pressure</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | double |
| **Value Type** | array |
| **_FillValue** | -999. |
| **Description** | An array containing the time-series of measured and/or interpolated pressures for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double pressure(time) ;
        pressure:_FillValue = -999. ;
        pressure:accuracy = " " ;
        pressure:ancillary_variables = "pressure_qc" ;
        pressure:comment = " " ;
        pressure:instrument = "instrument_ctd" ;
        pressure:long_name = "Pressure" ;
        pressure:observation_type = "measured" ;
        pressure:platform = "platform" ;
        pressure:positive = "down" ;
        pressure:precision = " " ;
        pressure:reference_datum = "sea-surface" ;
        pressure:resolution = " " ;
        pressure:standard_name = "sea_water_pressure" ;
        pressure:units = "dbar" ;
        pressure:valid_max = 2000 ;
        pressure:valid_min = 0 ;
```


#### <i>pressure_qc</i>



| | |
|-|-|
| **Dimension** | time |
| **Data Type** | byte |
| **Value Type** | array |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the values in the **pressure** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte pressure_qc(time) ;
        pressure_qc:_FillValue = -127b ;
        pressure_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        pressure_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        pressure_qc:long_name = "pressure Quality Flag" ;
        pressure_qc:standard_name = "sea_water_pressure status_flag" ;
        pressure_qc:valid_max = 9b ;
        pressure_qc:valid_min = 0b ;
```


#### <i>depth</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | double |
| **Value Type** | array |
| **_FillValue** | -999. |
| **Description** | An array containing the time-series of measured and/or interpolated depths for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double depth(time) ;
        depth:_FillValue = -999. ;
        depth:accuracy = " " ;
        depth:ancillary_variables = "depth_qc" ;
        depth:comment = " " ;
        depth:instrument = "instrument_ctd" ;
        depth:long_name = "Depth" ;
        depth:observation_type = "calculated" ;
        depth:platform = "platform" ;
        depth:positive = "down" ;
        depth:precision = " " ;
        depth:reference_datum = "sea-surface" ;
        depth:resolution = " " ;
        depth:standard_name = "depth" ;
        depth:units = "m" ;
        depth:valid_max = 2000 ;
        depth:valid_min = 0 ;
```


#### <i>depth_qc</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | byte |
| **Value Type** | array |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the values in the **depth** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte depth_qc(time) ;
        depth_qc:_FillValue = -127b ;
        depth_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        depth_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        depth_qc:long_name = "depth Quality Flag" ;
        depth_qc:standard_name = "depth status_flag" ;
        depth_qc:valid_max = 9b ;
        depth_qc:valid_min = 0b ;
```


#### <i>temperature</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | double |
| **Value Type** | array |
| **_FillValue** | -999. |
| **Description** | An array containing the temperature time-series for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double temperature(time) ;
        temperature:_FillValue = -999. ;
        temperature:accuracy = " " ;
        temperature:ancillary_variables = "temperature_qc" ;
        temperature:instrument = "instrument_ctd" ;
        temperature:long_name = "Temperature" ;
        temperature:observation_type = "measured" ;
        temperature:platform = "platform" ;
        temperature:precision = " " ;
        temperature:resolution = " " ;
        temperature:standard_name = "sea_water_temperature" ;
        temperature:units = "Celsius" ;
        temperature:valid_max = 40. ;
        temperature:valid_min = -5. ;
```


#### <i>temperature_qc</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | byte |
| **Value Type** | array |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the values in the **temperature** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte temperature_qc(time) ;
        temperature_qc:_FillValue = -127b ;
        temperature_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        temperature_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        temperature_qc:long_name = "temperature Quality Flag" ;
        temperature_qc:standard_name = "sea_water_temperature status_flag" ;
        temperature_qc:valid_max = 9b ;
        temperature_qc:valid_min = 0b ;
```


#### <i>conductivity</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | double |
| **Value Type** | array |
| **_FillValue** | -999. |
| **Description** | An array containing the conductivity time-series for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double conductivity(time) ;
        conductivity:_FillValue = -999. ;
        conductivity:accuracy = " " ;
        conductivity:ancillary_variables = "conductivity_qc" ;
        conductivity:instrument = "instrument_ctd" ;
        conductivity:long_name = "Conductivity" ;
        conductivity:observation_type = "measured" ;
        conductivity:platform = "platform" ;
        conductivity:precision = " " ;
        conductivity:resolution = " " ;
        conductivity:standard_name = "sea_water_electrical_conductivity" ;
        conductivity:units = "S m-1" ;
        conductivity:valid_max = 10. ;
        conductivity:valid_min = 0. ;
```


#### <i>conductivity_qc</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | byte |
| **Value Type** | array |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the values in the **conductivity** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte conductivity_qc(time) ;
        conductivity_qc:_FillValue = -127b ;
        conductivity_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        conductivity_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        conductivity_qc:long_name = "conductivity Quality Flag" ;
        conductivity_qc:standard_name = "sea_water_electrical_conductivity status_flag" ;
        conductivity_qc:valid_max = 9b ;
        conductivity_qc:valid_min = 0b ;
```


#### <i>salinity</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | double |
| **Value Type** | array |
| **_FillValue** | -999. |
| **Description** | An array containing the conductivity time-series for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double salinity(time) ;
        salinity:_FillValue = -999. ;
        salinity:accuracy = " " ;
        salinity:ancillary_variables = "salinity_qc" ;
        salinity:instrument = "instrument_ctd" ;
        salinity:long_name = "Salinity" ;
        salinity:observation_type = "calculated" ;
        salinity:platform = "platform" ;
        salinity:precision = " " ;
        salinity:resolution = " " ;
        salinity:standard_name = "sea_water_practical_salinity" ;
        salinity:units = "1" ;
        salinity:valid_max = 40. ;
        salinity:valid_min = 0. ;
```


#### <i>salinity_qc</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | byte |
| **Value Type** | array |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the values in the **salinity** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte salinity_qc(time) ;
        salinity_qc:_FillValue = -127b ;
        salinity_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        salinity_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        salinity_qc:long_name = "salinity Quality Flag" ;
        salinity_qc:standard_name = "sea_water_salinity status_flag" ;
        salinity_qc:valid_max = 9b ;
        salinity_qc:valid_min = 0b ;
```


#### <i>density</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | double |
| **Value Type** | array |
| **_FillValue** | -999. |
| **Description** | An array containing the conductivity time-series for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double density(time) ;
        density:_FillValue = -999. ;
        density:accuracy = " " ;
        density:ancillary_variables = "density_qc" ;
        density:instrument = "instrument_ctd" ;
        density:long_name = "Density" ;
        density:observation_type = "calculated" ;
        density:platform = "platform" ;
        density:precision = " " ;
        density:resolution = " " ;
        density:standard_name = "sea_water_density" ;
        density:units = "kg m-3" ;
        density:valid_max = 1040. ;
        density:valid_min = 1015. ;
```


#### <i>density_qc</i>

| | |
|-|-|
| **Dimension** | time |
| **Data Type** | byte |
| **Value Type** | array |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the values in the **density** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte density_qc(time) ;
        density_qc:_FillValue = -127b ;
        density_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        density_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        density_qc:long_name = "density Quality Flag" ;
        density_qc:standard_name = "sea_water_density status_flag" ;
        density_qc:valid_max = 9b ;
        density_qc:valid_min = 0b ;
```


### Dimensionless Profile Variables

The following variables are dimensionless and are used by the NGDAC to provide access to individual profiles from within the aggregated data sets. The **NGDAC** uses these variables to create a **profile** dimension in the aggregated data sets to provide access to the data on a profile-by-profile basis.

#### <i>profile_id</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | integer |
| **Value Type** | Scalar |
| **_FillValue** | -999 |
| **Description** | Unique identifier for the profile. The numbering can begin at 1 and be incremented for each successive profile contained in the trajectory or can contain the timestamp corresponding to the mid-point of the profile.

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 int profile_id ;
        profile_id:_FillValue = -999 ;
        profile_id:comment = "Sequential profile number within the trajectory. This value is unique in each file that is part of a single trajectory/deployment." ;
        profile_id:long_name = "Profile ID" ;
        profile_id:valid_max = 2147483647 ;
        profile_id:valid_min = 1 ;
```


#### <i>profile_time</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | double |
| **Value Type** | Scalar |
| **_FillValue** | -999. |
| **Description** | The time stamp at the mid-point of the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double profile_time ;
        profile_time:_FillValue = -999. ;
 profile_time:calendar = "gregorian" ;
        profile_time:comment = "Timestamp corresponding to the mid-point of the profile" ;
        profile_time:long_name = "Profile Center Time" ;
        profile_time:observation_type = "calculated" ;
        profile_time:platform = "platform" ;
        profile_time:standard_name = "time" ;
        profile_time:units = "seconds since 1970-01-01T00:00:00Z" ;
```


#### <i>profile_time_qc</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | byte |
| **Value Type** | scalar |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the value in the **profile_time** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte profile_time_qc ;
        profile_time_qc:_FillValue = -127b ;
        profile_time_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        profile_time_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        profile_time_qc:long_name = "profile_time Quality Flag" ;
        profile_time_qc:standard_name = "time status_flag" ;
        profile_time_qc:valid_max = 9b ;
        profile_time_qc:valid_min = 0b ;
```


#### <i>profile_lat</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | double |
| **Value Type** | Scalar |
| **_FillValue** | -999. |
| **Description** | The latitude at the mid-point of the profile. Since the glider is underwater at this point, this value is interpolated with the interpolation method left up to the data provider. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double profile_lat ;
        profile_lat:_FillValue = -999. ;
        profile_lat:comment = "Value is interpolated to provide an estimate of the latitude at the mid-point of the profile" ;
        profile_lat:long_name = "Profile Center Latitude" ;
        profile_lat:observation_type = "calculated" ;
        profile_lat:platform = "platform" ;
        profile_lat:standard_name = "latitude" ;
        profile_lat:units = "degrees_north" ;
        profile_lat:valid_max = 90. ;
        profile_lat:valid_min = -90. ;
```


#### <i>profile_lat_qc</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | byte |
| **Value Type** | scalar |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the value in the **profile_lat** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte profile_lat_qc ;
        profile_lat_qc:_FillValue = -127b ;
        profile_lat_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        profile_lat_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        profile_lat_qc:long_name = "profile_lat Quality Flag" ;
        profile_lat_qc:standard_name = "latitude status_flag" ;
        profile_lat_qc:valid_max = 9b ;
        profile_lat_qc:valid_min = 0b ;
```


#### <i>profile_lon</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | double |
| **Value Type** | Scalar |
| **_FillValue** | -999. |
| **Description** | The longitude at the mid-point of the profile. Since the glider is underwater at this point, this value is interpolated with the interpolation method left up to the data provider. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double profile_lon ;
        profile_lon:_FillValue = -999. ;
        profile_lon:comment = "Value is interpolated to provide an estimate of the longitude at the mid-point of the profile" ;
        profile_lon:long_name = "Profile Center Longitude" ;
        profile_lon:observation_type = "calculated" ;
        profile_lon:platform = "platform" ;
        profile_lon:standard_name = "longitude" ;
        profile_lon:units = "degrees_east" ;
        profile_lon:valid_max = 180. ;
        profile_lon:valid_min = -180. ;
```


#### <i>profile_lon_qc</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | byte |
| **Value Type** | scalar |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the value in the **profile_lon** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte profile_lon_qc ;
        profile_lon_qc:_FillValue = -127b ;
        profile_lon_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        profile_lon_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        profile_lon_qc:long_name = "profile_lon Quality Flag" ;
        profile_lon_qc:standard_name = "longitude status_flag" ;
        profile_lon_qc:valid_max = 9b ;
        profile_lon_qc:valid_min = 0b ;
```


#### <i>time_uv</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | double |
| **Value Type** | Scalar |
| **_FillValue** | -999. |
| **Description** | The time stamp of the calculated depth-averaged current for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double time_uv ;
        time_uv:_FillValue = -999. ;
        time_uv:calendar = "gregorian" ;
        time_uv:comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater. The value is calculated over the entire underwater segment, which may consist of 1 or more dives." ;
        time_uv:long_name = "Depth-Averaged Time" ;
        time_uv:observation_type = "calculated" ;
        time_uv:standard_name = "time" ;
        time_uv:units = "seconds since 1970-01-01T00:00:00Z" ;
```


#### <i>time_uv_qc</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | byte |
| **Value Type** | scalar |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the value in the **time_uv** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte time_uv_qc ;
        time_uv_qc:_FillValue = -127b ;
        time_uv_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        time_uv_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        time_uv_qc:long_name = "time_uv Quality Flag" ;
        time_uv_qc:standard_name = "time status_flag" ;
        time_uv_qc:valid_max = 9b ;
        time_uv_qc:valid_min = 0b ;
```


#### <i>lat_uv</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | double |
| **Value Type** | Scalar |
| **_FillValue** | -999. |
| **Description** | The latitude of the calculated depth-averaged current for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double lat_uv ;
        lat_uv:_FillValue = -999. ;
        lat_uv:comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater. The value is calculated over the entire underwater segment, which may consist of 1 or more dives." ;
        lat_uv:long_name = "Depth-Averaged Latitude" ;
        lat_uv:observation_type = "calculated" ;
        lat_uv:platform = "platform" ;
        lat_uv:standard_name = "latitude" ;
        lat_uv:units = "degrees_north" ;
        lat_uv:valid_max = 90. ;
        lat_uv:valid_min = -90. ;
```


#### <i>lat_uv_qc</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | byte |
| **Value Type** | scalar |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the value in the **lat_uv** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte lat_uv_qc ;
        lat_uv_qc:_FillValue = -127b ;
        lat_uv_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        lat_uv_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        lat_uv_qc:long_name = "lat_uv Quality Flag" ;
        lat_uv_qc:standard_name = "latitude status_flag" ;
        lat_uv_qc:valid_max = 9b ;
        lat_uv_qc:valid_min = 0b ;
```


#### <i>lon_uv</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | double |
| **Value Type** | Scalar |
| **_FillValue** | -999. |
| **Description** | The longitude of the calculated depth-averaged current for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double lon_uv ;
        lon_uv:_FillValue = -999. ;
        lon_uv:comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater. The value is calculated over the entire underwater segment, which may consist of 1 or more dives." ;
        lon_uv:long_name = "Depth-Averaged Longitude" ;
        lon_uv:observation_type = "calculated" ;
        lon_uv:platform = "platform" ;
        lon_uv:standard_name = "longitude" ;
        lon_uv:units = "degrees_east" ;
        lon_uv:valid_max = 180. ;
        lon_uv:valid_min = -180. ;
```


#### <i>lon_uv_qc</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | byte |
| **Value Type** | scalar |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the value in the **lon_uv** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte lon_uv_qc ;
        lon_uv_qc:_FillValue = -127b ;
        lon_uv_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        lon_uv_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        lon_uv_qc:long_name = "lon_uv Quality Flag" ;
        lon_uv_qc:standard_name = "longitude status_flag" ;
        lon_uv_qc:valid_max = 9b ;
        lon_uv_qc:valid_min = 0b ;
```


#### <i>u</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | double |
| **Value Type** | Scalar |
| **_FillValue** | -999. |
| **Description** | The eastward velocity component of the calculated depth-averaged current for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double u ;
        u:_FillValue = -999. ;
        u:comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater. The value is calculated over the entire underwater segment, which may consist of 1 or more dives." ;
        u:long_name = "Depth-Averaged Eastward Sea Water Velocity" ;
        u:observation_type = "calculated" ;
        u:platform = "platform" ;
        u:standard_name = "eastward_sea_water_velocity" ;
        u:units = "m s-1" ;
        u:valid_max = 10. ;
        u:valid_min = -10. ;
```


#### <i>u_qc</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | byte |
| **Value Type** | scalar |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the value in the **u** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte u_qc ;
        u_qc:_FillValue = -127b ;
        u_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        u_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        u_qc:long_name = "u Quality Flag" ;
        u_qc:standard_name = "eastward_sea_water_velocity status_flag" ;
        u_qc:valid_max = 9b ;
        u_qc:valid_min = 0b ;
```


#### <i>v</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | double |
| **Value Type** | Scalar |
| **_FillValue** | -999. |
| **Description** | The northward velocity component of the calculated depth-averaged current for the profile. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 double v ;
        v:_FillValue = -999. ;
        v:comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater. The value is calculated over the entire underwater segment, which may consist of 1 or more dives." ;
        v:long_name = "Depth-Averaged Northward Sea Water Velocity" ;
        v:observation_type = "calculated" ;
        v:platform = "platform" ;
        v:standard_name = "northward_sea_water_velocity" ;
        v:units = "m s-1" ;
        v:valid_max = 10. ;
        v:valid_min = -10. ;
```


#### <i>v_qc</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | byte |
| **Value Type** | scalar |
| **_FillValue** | -127b |
| **Description** | An array that contains values conveying information on the data quality status of the value in the **v** variable. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes:

```
 byte v_qc ;
        v_qc:_FillValue = -127b ;
        v_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
        v_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
        v_qc:long_name = "v Quality Flag" ;
        v_qc:standard_name = "northward_sea_water_velocity status_flag" ;
        v_qc:valid_max = 9b ;
        v_qc:valid_min = 0b ;
```


### Dimensionless Container Variables

The following variables are dimensionless container variables used to store meta data about the glider and instrumentation.

#### <i>platform</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | int |
| **Value Type** | Scalar |
| **_FillValue** | -999 |
| **Description** | Variable to store meta data about the glider platform that measured the profile. All of the attributes of this variable, with the exception of **comment** are **REQUIRED</b>. This variable contains a **wmo_id** attribute to store the **WMO ID** assigned to this glider by NDBC. The **WMO ID** is also stored as a global file attribute to allow for aggregations of all deployments from the platform with that **WMO ID</b>. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes and comments on values:

```
 int platform ;
        platform:_FillValue = -999 ;
        platform:comment = "Slocum Glider ru29" ; # Change
        platform:id = "ru29" ; # Change
        platform:instrument = "instrument_ctd" ;
        platform:long_name = "Rutgers University Slocum Glider ru29" ; # Change
        platform:type = "platform" ;
        platform:wmo_id = " " ; # WMO ID specific to this glider
```


#### <i>instrument_ctd</i>

| | |
|-|-|
| **Dimension** | None |
| **Data Type** | int |
| **Value Type** | Scalar |
| **_FillValue** | -999 |
| **Description** | Variable to store meta data about the CTD. The data provider should make an effort to include values for as many attributes as possible to create a complete meta data record, but are not required. |

[**CDL**](https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html) example with **REQUIRED** attributes and comments on values:

```
 int instrument_ctd ;
        instrument_ctd:_FillValue = -999 ;
        instrument_ctd:calibration_date = " " ; # Change to date formatted as YYYY-mm-ddTHH:MM:SSZ
        instrument_ctd:calibration_report = " " ; # Change to report url/location if available
        instrument_ctd:comment = "pumped CTD" ; # pumped or unpumped
        instrument_ctd:factory_calibrated = " " ; # Change to date formatted as YYYY-mm-ddTHH:MM:SSZ
        instrument_ctd:long_name = "Seabird Glider Payload CTD" ;
        instrument_ctd:make_model = "Seabird GPCTD" ; # CTD make and model
        instrument_ctd:platform = "platform" ;
        instrument_ctd:serial_number = " " ; # Provide serial number if available
        instrument_ctd:type = "platform" ;
```
