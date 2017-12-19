> [Wiki](https://github.com/kerfoot/ioosngdac/wiki) ▸ **NetCDF File Format Description**

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

## Introduction

This page provides and in-depth description of the NetCDF file format specification (__IOOS_Glider_NetCDF_v2.0.nc__) used by the __U.S. IOOS National Glider Data Assembly Center__ to archive and distribute real-time and delayed-mode glider data sets.  A thorough reading is __strongly__ recommended prior to beginning the [submission](https://github.com/kerfoot/ioosngdac/wiki/NGDAC-NetCDF-File-Submission-Process) process.  <b>Examples</b> of the file specification are available as <a target="_blank" href="https://github.com/kerfoot/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.nc">NetCDF</a>, <a target="_blank" href="https://github.com/kerfoot/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.cdl">CDL</a> and <a target="_blank" href="https://github.com/kerfoot/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.ncml">ncml</a> are available <a href="https://github.com/kerfoot/ioosngdac/tree/master/nc/template" target="_blank">here</a>.

The NetCDF file specification detailed below serves 2 primary purposes:
+ Provide a complete metadata record for all glider data submitted to the __NGDAC__ that can be harvested and stored by existing catalogs and registries. 
+ Provide a simple file format that is easily created by glider operators and data managers.  The flexibility provided by this specification allows for the creation of compound data products that result in easier, more intuitive methods of access by a wide range of end-users and in a variety of formats (i.e.: [csv](http://en.wikipedia.org/wiki/Comma-separated_values), [tsv](http://en.wikipedia.org/wiki/Tab-separated_values), [json](http://en.wikipedia.org/wiki/JSON), [geoJson](http://en.wikipedia.org/wiki/GeoJSON), etc.). 
+ Preserve the original resolution of the data sets.
 
Once the files have been uploaded by the individual glider operators, they are aggregated into a single data set (via [ERDDAP](http://coastwatch.pfeg.noaa.gov/erddap/information.html)) representing the entire __deployment/trajectory__.  These __deployment/trajectory__ datasets are publicly accessible via [ERDDAP](http://coastwatch.pfeg.noaa.gov/erddap/information.html) and [THREDDS](http://www.unidata.ucar.edu/software/thredds/current/tds/TDS.html) end-points.  The files submitted by glider operators are archived by the <b>NGDAC</b>, but are <b>not</b> available for public access in their original form.  The <b>NGDAC</b> uses a private [ERDDAP](http://coastwatch.pfeg.noaa.gov/erddap/information.html) server to aggregate the individual files into a single file representing the <b>trajectory</b>, in which all original metadata and sampling resolution is preserved.

## File Naming Conventions

The following list specifies the 2 file types which will be accepted by the <b>U.S IOOS National Glider Data Assembly Center</b> and the required naming conventions for each:
<ul>
<li><strong>glider_yyyymmddTHHMMSSZ_rt.nc</strong>: Data gathered in real-time or near real-time.  These files typically contain a subset of the full-resolution data provided in the delayed mode NetCDF files.</li>
<li><strong>glider_yyyymmddTHHMMSSZ_delayed.nc</strong>: Delayed-mode data set typically submitted after the glider is recovered. <b>**Delayed mode data may include a quality assessment but this is not required currently**</b></li>
</ul>

where
<dl>
<dt><b>glider</b></dt>
<dd> Identifying name or type abbreviation for the glider</dd>
<dt><b>yyyymmddTHHMMSSZ</b></dt>
<dd> <a href="http://en.wikipedia.org/wiki/ISO_8601">ISO 8601</a> formatted date representing the start time of the data acquisition, followed by <b>Z</b> to denote UTC time, not a local time zone.</dd>
<dt><b>'rt' or 'delayed'</b></dt>
<dd> string specifying real-time (during deployment) or delayed mode (post-recovery) data acquisition</dd>
</dl>

Ideally, the <strong>glider_yyyymmddTHHMMSS_rt.nc</strong> files will be provided by the individual operators during the deployment and the <strong>glider_yyyymmddTHHMMSS_delayed.nc</strong> files will be provided after the glider has been recovered and the full data set processed.  It is expected, where applicable, that all files will contain the appropriate <strong>VARIABLE_qc</strong> variables to convey some level of quality assurance for the data.  A discussion of these variables and their relationship to the sensor variables is found [below](#variables).

## Global Attributes

The following is the list of required global attributes that must be included in each NetCDF file submitted to the __NGDAC__.  This list was created from a variety of sources with the goal of providing a complete metadata record of the data set.  More information on these sources can be found at the following locations:
* <strong>CF1.6</strong> Section 2.6 of the current (v1.6) Climate and Forecast [conventions](http://cf-pcmdi.llnl.gov/documents/cf-conventions/1.6/cf-conventions.html#description-of-file-contents)
* <strong>ACDD</strong> Attribute Conventions for Dataset Discovery [Home page](http://wiki.esipfed.org/index.php?title=Category:Attribute_Conventions_Dataset_Discovery) and [Current Standard](http://wiki.esipfed.org/index.php/Attribute_Convention_for_Data_Discovery_%28ACDD%29) 
* <strong>NODC</strong> Guidance from NOAA's National Oceanographic Data Center on netCDF templates to promote good stewardship and archiving.  [NODC Templates](http://www.nodc.noaa.gov/data/formats/netcdf/) and [global attribute suggestions](http://www.nodc.noaa.gov/data/formats/netcdf/#guidancetable).
* <strong>IMOS/ANFOG</strong> IMOS Data Management manual version [3.1](http://imos.org.au/fileadmin/user_upload/shared/ANFOG/ANFOG_data_management3_1.pdf)
* <strong>IOOS</strong> Internal discussion within the IOOS Glider Data Team.

### Caveats

There are a few __important__ points to mention with regards to global attributes:

1. All attributes listed below are __REQUIRED__ and should have meaningful values assigned to them.  In the event that a meaningful value cannot be assigned, set the value to a single whitespace character enclosed in double quotes.  For example, if the data set has not been modified, you should set the __date_modified__ attribute value to __" "__.
2. For attributes with timestamp values (i.e.: __date_created__, __date_modified__, __date_issued__), use the <a href="http://en.wikipedia.org/wiki/ISO_8601#General_principles">ISO 8601:2004 'extended' format</a>.  This format has the general form: __YYYY-MM-DDThh:mm:ssZ__.
3. All global attributes must be string attributes.  
4. You may or may not notice the absence of a number of global attributes, particularly related to temporal and spatial extent (i.e.: __geospatial_lat_min__, __geospatial_vertical_min__, __time_coverage_start__, etc.), from this list.  The __NGDAC__ will add these global attributes and assign appropriate values to them prior to making the aggregated data sets available to the public.
5. The name and a description of each attribute are listed below.  An example is given where the selection of an appropriate value may be unclear.  Please use the specified __Value__ listed under the attribute name for the following attributes: __Conventions__, __Metadata_Conventions__, __format_version__, __standard_name_vocabulary__.

### Description & Examples of Required Global Attributes

<dl>
<dt><b>Conventions</b>:</dt>
<dd>
Version of the <a href="http://cfconventions.org/">Climate and Forecast metadata conventions</a> followed by the file format specification.
</dd>
<dd>
<b>Value</b>: "CF-1.6"
</dd>

<dt><b>Metadata_Conventions</b>:</dt>
<dd>
Unidata NetCDF group's <a href="https://geo-ide.noaa.gov/wiki/index.php?title=NetCDF_Attribute_Convention_for_Dataset_Discovery">Attribute Conventions for Dataset Discovery</a>.  These conventions identify and define a list of NetCDF global attributes recommended for describing a NetCDF dataset to discovery systems such as Digital Libraries. Software tools will use these attributes for extracting metadata from datasets, and exporting to Dublin Core, DIF, ADN, FGDC, ISO 19115 etc. metadata formats.
</dd>
<dd>
<b>Value</b>: "CF-1.6, Unidata Dataset Discovery v1.0"
</dd>

<dt><b>acknowledgement</b>:</dt>
<dd>
String used to properly acknowledge use of the data.
</dd>
<dd>
<b>Example</b>: "This work supported by funding from NOAA"
</dd>

<dt><b>comment</b>:<dt>
<dd>
Free-form field used to provide additional information on the data set
</dd>

<dt><b>contributor_name</b>:</dt>
<dd>
A comma separated list of contributors to this data set.
</dd>
<dd>
<b>Example</b>: "Jerry Garcia, Bob Weir, Bill Graham"
</dd>

<dt><b>contributor_role</b></dt>
<dd>
A comma separated list of the roles of those specified using the <b>contributor_name</b> attribute.
</dd>
<dd>
<b>Example</b>: "Principal Investigator, Principal Investigator, Data Manager"
</dd>

<dt><b>creator_email</b>:</dt>
<dd>
Email address for person who collected the data.
</dd>

<dt><b>creator_name</b>:</dt>
<dd>
Name of the person who collected the data.
</dd>

<dt><b>creator_url</b>:</dt>
<dd>
URL for person who collected the data.
</dd>

<dt><b>date_created</b>:</dt>
<dd>
Creation date of the file.  Use the <a href="http://en.wikipedia.org/wiki/ISO_8601">ISO 8601</a>:2004 Extended date time format.
</dd>
<dd>
<b>Example</b>: "1977-05-08T20:00:00Z"
</dd>

<dt><b>date_issued</b>:</dt>
<dd>
The date on which this data was formally issued.  Use the <a href="http://en.wikipedia.org/wiki/ISO_8601">ISO 8601</a>:2004 Extended date time format.
</dd>
<dd>
<b>Example</b>: "1992-06-25T20:00:00Z"
</dd>

<dt><b>date_modified</b>:</dt>
<dd>
Modification date of the file, if any.  Use the <a href="http://en.wikipedia.org/wiki/ISO_8601">ISO 8601</a>:2004 Extended date time format.

<b>Example</b>: "1978-06-04T20:00:00Z"
</dd>

<dt><b>format_version</b>:</dt>
<dd>
NetCDF file format version.
</dd>
<dd>
<b>Value</b>: "IOOS_Glider_NetCDF_v2.0.nc"
</dd>

<dt><b>history</b>:</dt>
<dd>
This is String with one or more lines, each of which has
the <a href="http://en.wikipedia.org/wiki/ISO_8601">ISO 8601</a>:2004 Extended date time and the
name and command line parameters of the program used to
create or change the data and/or other information about the change.
</dd>
<dd>
<b>Example</b>: "2014-07-21T00:00:00Z: /bin/writeIoosNc.py"
</dd>

<dt><b>id</b>:</dt>
<dd>
A human readable unique identifier for data set.  We recommend using the <b>trajectory</b> variable string name, which must have the following format:
<br />
<b>glider-YYYYmmddTHHMM</b>.
<br />
Where <b>glider</b> is the name of the glider and <b>YYYYmmddTHHMM</b> is the deployment date/time.
</dd>
<dd>
<b>Example</b>: "ru30-20140101T0000"
</dd>

<dt><b>institution</b>:</dt>
<dd>
Institution of the person or group that collected the data.  This value should be identical to the "Operator" specified on the http://gliders.ioos.us deployment page.
</dd>
<dd>
<b>Example</b>: "Rutgers University"
</dd>

<dt><b>keywords</b>:</dt>
<dd>
A comma separated list of keywords coming from the <b>keywords_vocabulary</b>.
</dd>
<dd>
<b>Example</b>: "AUVS > Autonomous Underwater Vehicles, Oceans > Ocean Pressure > Water Pressure, Oceans > Ocean Temperature > Water Temperature, Oceans > Salinity/Density > Conductivity, Oceans > Salinity/Density > Density, Oceans > Salinity/Density > Salinity"
</dd>

<dt><b>keywords_vocabulary</b>:</dt>
<dd>
Identifies the controlled keyword vocabulary used to specify the values within the <b>keywords</b> attribute.
</dd>
<dd>
<b>Example</b>: "GCMD Science Keywords"
</dd>

<dt><b>license</b>:</dt>
<dd>
Describe the restrictions to data access and distribution.
</dd>
<dd>
<b>Example</b>: "This data may be redistributed and used without restriction."
</dd>

<dt><b>metadata_link</b>:</dt>
<dd>
This attribute provides a link to a complete metadata record for this data set or the collection that contains this data set.
</dd>

<dt><b>naming_authority</b>:</dt>
<dd>
Backward URL of institution.
</dd>
<dd>
<b>Example</b>: "edu.rutgers.marine.rucool"
</dd>

<dt><b>platform_type</b>:</dt>
<dd>
Glider type.
</dd>
<dd>
<b>Example</b>: "Seaglider"
<br />
<b>Example</b>: "Spray Glider"
<br />
<b>Example</b>: "Slocum Glider"
</dd>

<dt><b>processing_level</b>:</dt>
<dd>
Provide a description of the processing or quality control level of the data.
</dd>
<dd>
<b>Example</b>: "Data provided as is with no expressed or implied assurance of quality assurance or quality control."
</dd>

<dt><b>project</b>:</dt>
<dd>
Project the data was collected under.
</dd>
<dd>
<b>Example</b>: "TEMPESTS"
</dd>

<dt><b>publisher_email</b>:</dt>
<dd>
Email address of the publisher of the data.
</dd>

<dt><b>publisher_name</b>:</dt>
<dd>
Name of the publisher of the data.
</dd>

<dt><b>publisher_url</b>:</dt>
<dd>
A URL for the publisher of the data.
</dd>

<dt><b>references</b>:</dt>
<dd>
Published or web-based references that describe the data or methods used to produce it.
</dd>

<dt><b>sea_name</b>:</dt>
<dd>
The names of the sea in which the data were collected. Use NODC sea names table.  Currently located at: <a target="_blank" href="http://www.nodc.noaa.gov/General/NODC-Archive/seanamelist.txt">http://www.nodc.noaa.gov/General/NODC-Archive/seanamelist.txt</a>.
</dd>

<dt><b>source</b>:</dt>
<dd>
The input data sources regardless of the method of production method used.
</dd>
<dd>
<b>Example</b>: "Observational data from a profiling glider."
</dd>

<dt><b>standard_name_vocabulary</b>:</dt>
<dd>
Version of CF standard names used for variables.  <a href="http://cfconventions.org/standard-names.html">Current standard name table</a> 
</dd>
<dd>
CF Standard Name Table v27
</dd>

<dt><b>summary</b>:</dt>
<dd>
Provide a useful summary or abstract for the data in the file.  This summary is used as the primary piece of information describing the data set for discovery and archiving purposes.  As such, careful thought should be put into constructing the summary.  
</dd>
<dd>
<b>Example</b>: "Slocum glider dataset gathered as part of the TEMPESTS (The Experiment to Measure and Predict East coast STorm Strength), funded by NOAA through CINAR (Cooperative Institute for the North Atlantic Region).  This dataset contains physical oceanographic measurements of temperature, conductivity, salinity, density and estimates of depth-average currents."
</dd>
<dd>
Regardless of the summary added by the data provider, the following summary is added to this attribute prior to archiving by NCEI:
<p>
<b>Addendum:</b> The Integrated Ocean Observing System's National Glider Data Assembly Center receives sets of individual NetCDF     files comprising an individual glider deployment from data operators and providers around the world. These files are checked for compliance and then aggregated into a single data set representing the entire deployment and made available via ERRDAP and THREDDS end points, making the data sets available to the public. Currently, the data sets provide measurements of physical oceanographic properties (temperature, salinity, conductivity and density). Future plans, currently under development, include providing access to biological and chemical properties. Once the deployment has been completed, as specified by the glider operator or data provider, the data set is marked for archiving, at which point it is added to the National Centers for Environmental Information (NCEI, formerly NODC) data archive to create a permanent archive of the data set.
</p>
</dd>

<dt><b>title</b>:</dt>
<dd>
We recommend using the <b>trajectory</b> variable string name, which must have the following format:
<br />
<b>glider-YYYYmmddTHHMM</b>.
<br />
Where <b>glider</b> is the name of the glider and <b>YYYYmmddTHHMM</b> is the deployment date/time.
</dd>
<dd>
<b>Example</b>: "ru30-20140101T0000"
</dd>

<dt><b>wmo_id</b>:</dt>
<dd>
String specifying the <a href="http://www.wmo.int/pages/prog/amp/mmop/wmo-number-rules.html">WMO ID</a> used to identify this platform.  Must be specified as a string attribute.  Each <a href="http://www.wmo.int/pages/prog/amp/mmop/wmo-number-rules.html">WMO ID</a> is unique to an individual glider deployed in a specific location and must be requested from the <b>NGDAC</b> administrator.
</dd>
<dd>
<b>Example</b>: "4801518"
</dd>

</dl>

## Variables

The NetCDF file specification contains 3 core variable types which relate to how the individual NetCDF files are aggregated by the __NGDAC__:

+ [time-series](#time-series-variables): dimensioned along the time axis to provide access to the data as time-series.
+ [profile](#dimensionless-profile-variables): dimensionless variables that provide access to data on a profile-by-profile basis
+ [container](#dimensionless-container-variables): dimensionless variables used to capture meta data regarding the platform and instrumentation on board the glider.

Most of the __time-series__ variables and many of the __profile__ variables have corresponding data quality variables, which are referenced via the __ancillary_variables__ variable attribute.  The dimensions of these variables are the same as the variables they convey quality information about.

While no CF standard names exist for these flags, CF conventions allow the use of a [standard_name modifier](http://cfconventions.org/Data/cf-convetions/cf-conventions-1.7/build/cf-conventions.html#standard-name-modifiers) to be appended to the corresponding variable's standard name to create the standard name for the quality control flag.  For example, the __temperature__ variable has a corresponding data quality variable (__temperature_qc__).  The __standard_name__ attribute contains the CF standard name of the variable it references with __status_flag__ appeneded, i.e.: __temperature__ __status_flag__

The following is a list and description of all variables and corresponding variable attributes that are __REQUIRED__ for the file to be accepted by the __NGDAC__.  An CDL description of each variable is located below the formal description.  Examples of the various attributes have been provided for reference, but each data provider is encouraged to modify these values if they feel it is necessary, particularly for the following attributes:

+ __comment__
+ __valid_min__
+ __valid_max__
+ __accuracy__
+ __precision__
+ __resolution__
+ __platform:wmo_id__
+ __platform:id__
+ __platform:long_name__
+ All __instrument_ctd__ attributes except __instrument_ctd:platform__


<b>Examples</b> of the file specification are available as <a target="_blank" href="https://github.com/kerfoot/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.nc">NetCDF</a>, <a target="_blank" href="https://github.com/kerfoot/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.cdl">CDL</a> and <a target="_blank" href="https://github.com/kerfoot/ioosngdac/blob/master/nc/template/IOOS_Glider_NetCDF_v2.0.ncml">ncml</a> are available <a href="https://github.com/kerfoot/ioosngdac/tree/master/nc/template" target="_blank">here</a>.

### Dimensions

NetCDF files submitted by the individual glider operators contain 2 dimension variables:

+ __time__: time when the individual sensor record was recorded.
+ __traj_strlen__: string specifying the trajectory name.

According to [CF Conventions](http://cfconventions.org/Data/cf-convetions/cf-conventions-1.7/build/cf-conventions.html#idm43169986560), dimension variables are not allowed to have missing values (i.e.: _FillValue).

The aggregated data sets created by the __NGDAC__ contain the following additional dimensions to increase the data access methods and are __NOT__ included in the individual profile NetCDF files submitted by the glider operators:

+ __trajectory__
+ __profile__
+ __obs__
+ __wmo_id_strlen__

### Trajectory Variables

The __trajectory__ variable stores a character array that identifies the deployment during which the data was gathered.  This variable is used by the DAC to aggregate all individual NetCDF profiles containing the same trajectory value into a single trajectory profile data set.  This value should be a character array that uniquely identifies the deployment.  Each individual NetCDF file from the deployment data set must have the same value.

##### <i>trajectory</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>traj_strlen</td></tr>
<tr><th><b>Data Type</b></th><td>string stored as char array</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>""</td>
<tr><th><b>Description</b></th><td>String representation of the trajectory specified using the format: <b>GLIDER-YYYYmmddTHHMM</b>.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    char trajectory(traj_strlen) ;
		trajectory:cf_role = "trajectory_id" ;
		trajectory:comment = "A trajectory is a single deployment of a glider and may span multiple data files." ;
		trajectory:long_name = "Trajectory/Deployment Name" ;
</pre></dd>
</dl>

### Time-Series Variables

The following variables are dimensioned along the time axis.

##### <i>time</i>

<b>IMPORTANT: The CF specification does not allow coordinate variables to contain missing/_FillValue values.</b> 

<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>Description</b></th><td>An array containing the time stamp corresponding to the acquisition of the sensor data for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    double time(time) ;
		time:ancillary_variables = "time_qc" ;
		time:calendar = "gregorian" ;
		time:long_name = "Time" ;
		time:observation_type = "measured" ;
		time:standard_name = "time" ;
		time:units = "seconds since 1970-01-01T00:00:00Z" ;
</pre></dd>
</dl>

##### <i>time_qc</i>
<dl>
<dt></dt>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the values in the <b>time</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte time_qc(time) ;
		time_qc:_FillValue = -127b ;
		time_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		time_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		time_qc:long_name = "time Quality Flag" ;
		time_qc:standard_name = "time status_flag" ;
		time_qc:valid_max = 9b ;
		time_qc:valid_min = 0b ;

</pre></dd>
</dl>

##### <i>lat</i>
<dl>
<dt></dt>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>An array containing the time-series of measured and/or interpolated latitudes for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
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
</pre></dd>
</dl>

##### <i>lat_qc</i>
<dl>
<dt></dt>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the values in the <b>lat</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte latitude_qc(time) ;
		lat_qc:_FillValue = -127b ;
		lat_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		lat_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		lat_qc:long_name = "latitude Quality Flag" ;
		lat_qc:standard_name = "latitude status_flag" ;
		lat_qc:valid_max = 9b ;
		lat_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>lon</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>An array containing the time-series of measured and/or interpolated longitudes for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
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
</pre></dd>
</dl>

##### <i>lon_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the values in the <b>lon</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte lon_qc(time) ;
		lon_qc:_FillValue = -127b ;
		lon_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		lon_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		lon_qc:long_name = "longitude Quality Flag" ;
		lon_qc:standard_name = "longitude status_flag" ;
		lon_qc:valid_max = 9b ;
		lon_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>pressure</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>An array containing the time-series of measured and/or interpolated pressures for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
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
</pre></dd>
</dl>

##### <i>pressure_qc</i>
<dl>
<dt></dt>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the values in the <b>pressure</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte pressure_qc(time) ;
		pressure_qc:_FillValue = -127b ;
		pressure_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		pressure_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		pressure_qc:long_name = "pressure Quality Flag" ;
		pressure_qc:standard_name = "sea_water_pressure status_flag" ;
		pressure_qc:valid_max = 9b ;
		pressure_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>depth</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>An array containing the time-series of measured and/or interpolated depths for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
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
</pre></dd>
</dl>

##### <i>depth_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the values in the <b>depth</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte depth_qc(time) ;
		depth_qc:_FillValue = -127b ;
		depth_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		depth_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		depth_qc:long_name = "depth Quality Flag" ;
		depth_qc:standard_name = "depth status_flag" ;
		depth_qc:valid_max = 9b ;
		depth_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>temperature</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>An array containing the temperature time-series for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
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
</pre></dd>
</dl>

##### <i>temperature_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the values in the <b>temperature</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte temperature_qc(time) ;
		temperature_qc:_FillValue = -127b ;
		temperature_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		temperature_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		temperature_qc:long_name = "temperature Quality Flag" ;
		temperature_qc:standard_name = "sea_water_temperature status_flag" ;
		temperature_qc:valid_max = 9b ;
		temperature_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>conductivity</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>An array containing the conductivity time-series for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
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
</pre></dd>
</dl>

##### <i>conductivity_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the values in the <b>conductivity</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte conductivity_qc(time) ;
		conductivity_qc:_FillValue = -127b ;
		conductivity_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		conductivity_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		conductivity_qc:long_name = "conductivity Quality Flag" ;
		conductivity_qc:standard_name = "sea_water_electrical_conductivity status_flag" ;
		conductivity_qc:valid_max = 9b ;
		conductivity_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>salinity</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>An array containing the conductivity time-series for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
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
</pre></dd>
</dl>

##### <i>salinity_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the values in the <b>salinity</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte salinity_qc(time) ;
		salinity_qc:_FillValue = -127b ;
		salinity_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		salinity_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		salinity_qc:long_name = "salinity Quality Flag" ;
		salinity_qc:standard_name = "sea_water_salinity status_flag" ;
		salinity_qc:valid_max = 9b ;
		salinity_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>density</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>An array containing the conductivity time-series for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
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
</pre></dd>
</dl>

##### <i>density_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>time</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>array</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the values in the <b>density</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte density_qc(time) ;
		density_qc:_FillValue = -127b ;
		density_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		density_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		density_qc:long_name = "density Quality Flag" ;
		density_qc:standard_name = "sea_water_density status_flag" ;
		density_qc:valid_max = 9b ;
		density_qc:valid_min = 0b ;
</pre></dd>
</dl>

###Dimensionless Profile Variables###

The following variables are dimensionless and are used by the NGDAC to provide access to individual profiles from within the aggregated data sets.  The __NGDAC__ uses these variables to create a __profile__ dimension in the aggregated data sets to provide access to the data on a profile-by-profile basis.

##### <i>profile_id</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>integer</td></tr>
<tr><th><b>Value Type</b></th><td>Scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-999</td>
<tr><th><b>Description</b></th><td>Unique identifier for the profile.  The numbering must begin at 1 and is incremented for each successive profile contained in the trajectory.  The ordering of the numbering does not necessarily correspond to the profile's temporal position in the trajectory.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    int profile_id ;
		profile_id:_FillValue = -999 ;
		profile_id:comment = "Sequential profile number within the trajectory.  This value is unique in each file that is part of a single trajectory/deployment." ;
		profile_id:long_name = "Profile ID" ;
		profile_id:valid_max = 2147483647 ;
		profile_id:valid_min = 1 ;
</pre></dd>
</dl>

##### <i>profile_time</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>Scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>The time stamp at the mid-point of the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    double profile_time ;
		profile_time:_FillValue = -999. ;
                profile_time:calendar = "gregorian" ;
		profile_time:comment = "Timestamp corresponding to the mid-point of the profile" ;
		profile_time:long_name = "Profile Center Time" ;
		profile_time:observation_type = "calculated" ;
		profile_time:platform = "platform" ;
		profile_time:standard_name = "time" ;
		profile_time:units = "seconds since 1970-01-01T00:00:00Z" ;
</pre></dd>
</dl>

##### <i>profile_time_qc</i>
<d1>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the value in the <b>profile_time</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte profile_time_qc ;
		profile_time_qc:_FillValue = -127b ;
		profile_time_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		profile_time_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		profile_time_qc:long_name = "profile_time Quality Flag" ;
		profile_time_qc:standard_name = "time status_flag" ;
		profile_time_qc:valid_max = 9b ;
		profile_time_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>profile_lat</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>Scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>The latitude at the mid-point of the profile.  Since the glider is underwater at this point, this value is interpolated with the interpolation method left up to the data provider.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
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
</pre></dd>
</dl>

##### <i>profile_lat_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the value in the <b>profile_lat</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte profile_lat_qc ;
		profile_lat_qc:_FillValue = -127b ;
		profile_lat_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		profile_lat_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		profile_lat_qc:long_name = "profile_lat Quality Flag" ;
		profile_lat_qc:standard_name = "latitude status_flag" ;
		profile_lat_qc:valid_max = 9b ;
		profile_lat_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>profile_lon</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>Scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>The longitude at the mid-point of the profile.  Since the glider is underwater at this point, this value is interpolated with the interpolation method left up to the data provider.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
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
</pre></dd>
</dl>

##### <i>profile_lon_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the value in the <b>profile_lon</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte profile_lon_qc ;
		profile_lon_qc:_FillValue = -127b ;
		profile_lon_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		profile_lon_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		profile_lon_qc:long_name = "profile_lon Quality Flag" ;
		profile_lon_qc:standard_name = "longitude status_flag" ;
		profile_lon_qc:valid_max = 9b ;
		profile_lon_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>time_uv</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>Scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>The time stamp of the calculated depth-averaged current for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    double time_uv ;
		time_uv:_FillValue = -999. ;
		time_uv:calendar = "gregorian" ;
		time_uv:comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater.  The value is calculated over the entire underwater segment, which may consist of 1 or more dives." ;
		time_uv:long_name = "Depth-Averaged Time" ;
		time_uv:observation_type = "calculated" ;
		time_uv:standard_name = "time" ;
		time_uv:units = "seconds since 1970-01-01T00:00:00Z" ;
</pre></dd>
</dl>

##### <i>time_uv_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the value in the <b>time_uv</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte time_uv_qc ;
		time_uv_qc:_FillValue = -127b ;
		time_uv_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		time_uv_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		time_uv_qc:long_name = "time_uv Quality Flag" ;
		time_uv_qc:standard_name = "time status_flag" ;
		time_uv_qc:valid_max = 9b ;
		time_uv_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>lat_uv</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>Scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>The latitude of the calculated depth-averaged current for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    double lat_uv ;
		lat_uv:_FillValue = -999. ;
		lat_uv:comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater.  The value is calculated over the entire underwater segment, which may consist of 1 or more dives." ;
		lat_uv:long_name = "Depth-Averaged Latitude" ;
		lat_uv:observation_type = "calculated" ;
		lat_uv:platform = "platform" ;
		lat_uv:standard_name = "latitude" ;
		lat_uv:units = "degrees_north" ;
		lat_uv:valid_max = 90. ;
		lat_uv:valid_min = -90. ;
</pre></dd>
</dl>

##### <i>lat_uv_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the value in the <b>lat_uv</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte lat_uv_qc ;
		lat_uv_qc:_FillValue = -127b ;
		lat_uv_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		lat_uv_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		lat_uv_qc:long_name = "lat_uv Quality Flag" ;
		lat_uv_qc:standard_name = "latitude status_flag" ;
		lat_uv_qc:valid_max = 9b ;
		lat_uv_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>lon_uv</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>Scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>The longitude of the calculated depth-averaged current for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    double lon_uv ;
		lon_uv:_FillValue = -999. ;
		lon_uv:comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater.  The value is calculated over the entire underwater segment, which may consist of 1 or more dives." ;
		lon_uv:long_name = "Depth-Averaged Longitude" ;
		lon_uv:observation_type = "calculated" ;
		lon_uv:platform = "platform" ;
		lon_uv:standard_name = "longitude" ;
		lon_uv:units = "degrees_east" ;
		lon_uv:valid_max = 180. ;
		lon_uv:valid_min = -180. ;
</pre></dd>
</dl>

##### <i>lon_uv_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the value in the <b>lon_uv</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte lon_uv_qc ;
		lon_uv_qc:_FillValue = -127b ;
		lon_uv_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		lon_uv_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		lon_uv_qc:long_name = "lon_uv Quality Flag" ;
		lon_uv_qc:standard_name = "longitude status_flag" ;
		lon_uv_qc:valid_max = 9b ;
		lon_uv_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>u</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>Scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>The eastward velocity component of the calculated depth-averaged current for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    double u ;
		u:_FillValue = -999. ;
		u:comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater.  The value is calculated over the entire underwater segment, which may consist of 1 or more dives." ;
		u:long_name = "Depth-Averaged Eastward Sea Water Velocity" ;
		u:observation_type = "calculated" ;
		u:platform = "platform" ;
		u:standard_name = "eastward_sea_water_velocity" ;
		u:units = "m s-1" ;
		u:valid_max = 10. ;
		u:valid_min = -10. ;
</pre></dd>
</dl>

##### <i>u_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the value in the <b>u</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte u_qc ;
		u_qc:_FillValue = -127b ;
		u_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		u_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		u_qc:long_name = "u Quality Flag" ;
		u_qc:standard_name = "eastward_sea_water_velocity status_flag" ;
		u_qc:valid_max = 9b ;
		u_qc:valid_min = 0b ;
</pre></dd>
</dl>

##### <i>v</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>double</td></tr>
<tr><th><b>Value Type</b></th><td>Scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-999.</td>
<tr><th><b>Description</b></th><td>The northward velocity component of the calculated depth-averaged current for the profile.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    double v ;
		v:_FillValue = -999. ;
		v:comment = "The depth-averaged current is an estimate of the net current measured while the glider is underwater.  The value is calculated over the entire underwater segment, which may consist of 1 or more dives." ;
		v:long_name = "Depth-Averaged Northward Sea Water Velocity" ;
		v:observation_type = "calculated" ;
		v:platform = "platform" ;
		v:standard_name = "northward_sea_water_velocity" ;
		v:units = "m s-1" ;
		v:valid_max = 10. ;
		v:valid_min = -10. ;
</pre></dd>
</dl>

##### <i>v_qc</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>byte</td></tr>
<tr><th><b>Value Type</b></th><td>scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-127b</td>
<tr><th><b>Description</b></th><td>An array that contains values conveying information on the data quality status of the value in the <b>v</b> variable.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes:
<pre>
    byte v_qc ;
		v_qc:_FillValue = -127b ;
		v_qc:flag_meanings = "no_qc_performed good_data probably_good_data bad_data_that_are_potentially_correctable bad_data value_changed not_used not_used interpolated_value missing_value" ;
		v_qc:flag_values = 0b, 1b, 2b, 3b, 4b, 5b, 6b, 7b, 8b, 9b ;
		v_qc:long_name = "v Quality Flag" ;
		v_qc:standard_name = "northward_sea_water_velocity status_flag" ;
		v_qc:valid_max = 9b ;
		v_qc:valid_min = 0b ;
</pre></dd>
</dl>

###Dimensionless Container Variables###

The following variables are dimensionless container variables used to store meta data about the glider and instrumentation.

##### <i>platform</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>int</td></tr>
<tr><th><b>Value Type</b></th><td>Scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-999</td>
<tr><th><b>Description</b></th><td>Variable to store meta data about the glider platform that measured the profile.  All of the attributes of this variable, with the exception of <b>comment</b> are <b>REQUIRED</b>.  This variable contains a <b>wmo_id</b> attribute to store the <b>WMO ID</b> assigned to this glider by NDBC.  The <b>WMO ID</b> is also stored as a global file attribute to allow for aggregations of all deployments from the platform with that <b>WMO ID</b>.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes and comments on values:
<pre>
    int platform ;
		platform:_FillValue = -999 ;
		platform:comment = "Slocum Glider ru29" ; # Change
		platform:id = "ru29" ; # Change
		platform:instrument = "instrument_ctd" ;
		platform:long_name = "Rutgers University Slocum Glider ru29" ; # Change
		platform:type = "platform" ;
		platform:wmo_id = " " ; # WMO ID specific to this glider
</pre></dd>
</dl>

##### <i>instrument_ctd</i>
<dl>
<dd>
<table>
<tr><th><b>Dimension</b></th><td>None</td></tr>
<tr><th><b>Data Type</b></th><td>int</td></tr>
<tr><th><b>Value Type</b></th><td>Scalar</td></tr>
<tr><th><b>_FillValue</b></th><td>-999</td>
<tr><th><b>Description</b></th><td>Variable to store meta data about the CTD.  The data provider should make an effort to include values for as many attributes as possible to create a complete meta data record, but are not required.</td></tr>
</table>
</dd>
<dd>
<a href="https://www.unidata.ucar.edu/software/netcdf/docs/netcdf/Data-Model.html">CDL</a> example with <b>REQUIRED</b> attributes and comments on values:
<pre>
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
</pre></dd>

</dl>