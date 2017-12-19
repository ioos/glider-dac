> [Wiki](https://github.com/kerfoot/ioosngdac/wiki) ▸ **NGDAC File Submission Process**

This page provides a detailed description of the end-to-end process of becoming a data provider, registering new glider deployments and submitting [NetCDF](https://github.com/kerfoot/ioosngdac/wiki/NetCDF-File-Format-Description) files to the <b>U.S. IOOS National Glider Data Assembly Center</b>.

Following a __thorough__ reading, all additional questions/concerns/suggestions should be directed to:

    ioos.glider.data.providers@noaa.gov

A consolidated list of the links referenced below can be found [here](https://github.com/ioos/ioosngdac/wiki/Links-for-Data-Providers#links).

# Contents

+ [Data Provider Registration](#data-provider-registration)
+ [New Deployment Registration](#new-deployment-registration)
+ [Submission of NetCDF Files](#submission-of-netcdf-files)
+ [Dataset Status](#dataset-status)
+ [Dataset Archiving](#dataset-archiving)

## Data Provider Registration

You must register as a data provider and receive a user account in order to contribute data sets to the <b>IOOS Glider Data Assembly Center</b>.  The following contact information is required:

+ Contact name
+ Contact organization
+ Email address
+ Telephone number
 
and all user account requests should be emailed to:

    glider.dac.support@noaa.gov

<b>New user accounts are typically created the same day they are received</b>.

## New Deployment Registration

Data providers can register deployments after the user account has been created.  New deployment registration is a 1 or 2 step process, depending on whether the deployment is current or historical.  If the deployment is current or in the future and you would like the data to be released on the <b>Global Telecommunication System (GTS)</b>, you must request a [WMO id](http://www.wmo.int/pages/prog/amp/mmop/buoy-ids.html) id for the glider.  This ID must be referenced as a [global](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2#description--examples-of-required-global-attributes) attribute as well as an attribute of the file's [platform](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2#platform) variable in each NetCDF file uploaded to the <b>NGDAC</b>.

The next step is to register the deployment with the <b>NGDAC</b>.

### Requesting a WMO ID

In order for the datasets to be released to the [Global Telecommunication System](http://www.wmo.int/pages/prog/www/TEM/index_en.html), the glider must be assigned a <b>WMO ID</b>.  All <b>WMO ID</b> requests should be sent to:

    ioos.glider.data@noaa.gov

The following information must be provided for each request:
+ Data provider
+ Glider name
+ Approximate deployment date
+ Approximate deployment location (GPS coordinates)

Once the request is received, it will be forwarded to the [National Data Buoy Center](http://www.ndbc.noaa.gov/) and the assigned <b>WMO ID</b> will be sent to the requestor/data provider.

<b>IMPORTANT</b>: WMO ids are assigned based on the [WMO region](http://en.wikipedia.org/wiki/Location_identifier#WMO_station_identifiers) in which the glider is deployed.  Once assigned, the WMO id may be used on successive deployments of the same glider provided it is deployed in the same WMO region.  <b>You do not need to acquire a different WMO id each time the glider is deployed, provided it's deployed in the same WMO region.</b>

### Deployment Creation

Deployments are registered and managed via a [web page](http://data.ioos.us/gliders/providers). Each deployment must be registered by the data provider <b>before</b> any NetCDF files are uploaded.  The deployment registration process is as follows:

1. Log in using your data provider credentials.
2. Click the __Your Deployments__ link.  A deployment registration form will be displayed.
3. Specify a unique deployment name using the following convention:
    <b>GLIDER-YYYYmmddTHHMM</b>

    Where <b>GLIDER</b> is the actual name of the glider and <b>YYYYmmddTHHMM</b> is the timestamp specifying  the start of the deployment.  This is also the value that should be assigned to the [trajectory](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2#trajectory) variable in each NetCDF file that is submitted to the DAC.  Enter the <b>WMO id</b> assigned to this glider for the new deployment in the form element. 

    <b>IMPORTANT</b>:
    This WMO id must also be referenced as a [global](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2#description--examples-of-required-global-attributes) attribute as well as an attribute of the file's [platform](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2#platform) variable in each NetCDF file uploaded to the <b>NGDAC</b>. 

4. Click __New Deployment__ to create the deployment.  This creates a directory on the IOOS Glider DAC FTP server using the specified deployment name.  This is the directory that the NetCDF files must be uploaded to.

    <b>IMPORTANT: New deployments cannot be created by logging into the ftp server.  All new deployments must be created via the process described above.</b>

5. After the deployment has been registered, click on the deployment name to take you to the deployment metadata page and specify the __operator__.  Once the deployment has been completed (i.e.: the glider has been recovered or the deployment has been completed), click the __Completed__ check box to denote that the data is ready for archiving by [NODC](http://www.nodc.noaa.gov).

## Submission of NetCDF Files

The data provider user account provides ftp push access to the directories created under the user's home directory.  The ftp url is:

    ftp://data.ioos.us

Here's an example of the ftp login process and the resulting directory structure:

    $ ftp -i data.ioos.us
    Connected to data.ioos.us (54.204.42.247).
    220 Welcome to the IOOS Glider DAC FTP Server
    Name (data.ioos.us:kerfoot): rutgers
    331 Please specify the password.
    Password:
    230 Login successful.
    Remote system type is UNIX.
    Using binary mode to transfer files.
    ftp> pwd
    257 "/"
    ftp> dir
    200 PORT command successful. Consider using PASV.
    150 Here comes the directory listing.
    drwxr-xr-x    2 ftp      ftp         77824 Dec 08 16:40 ru01-20140104T1621
    drwxr-xr-x    2 ftp      ftp          4096 Dec 08 16:41 ru01-20140120T1444
    drwxr-xr-x    2 ftp      ftp         57344 Dec 08 16:41 ru01-20140123T1250
    drwxr-xr-x    2 ftp      ftp         65536 Dec 08 16:41 ru01-20140217T1244
    drwxr-xr-x    2 ftp      ftp         36864 Jan 15 16:07 ru05-20150105T1600
    drwxr-xr-x    2 ftp      ftp         65536 Feb 02 13:41 ru05-20150115T1443
    
    226 Directory send OK.

New NetCDF files should be uploaded to the directory [created above](#deployment-creation).  For example, uploading files to the ru05-20150115T1443 deployment is done as follows:

    ftp> cd ru05-20150115T1443
    250 Directory successfully changed.
    ftp> lcd LOCAL_DIRECTORY
    Local directory now LOCAL_DIRECTORY
    ftp> mput *.nc
    
Please remember to use the [proper](https://github.com/ioos/ioosngdac/wiki/NGDAC-NetCDF-File-Format-Version-2#file-naming-conventions) file naming convention.

The resulting deployment directory structure will look something like this:

    /ru05-20150115T1443
        profile1.nc
        profile2.nc
        profile3.nc
        ...

A generic [ftp script](https://github.com/kerfoot/ioosngdac/blob/master/util/ncFtp2ngdac.pl), written in [Perl](http://www.perl.org/) is contained in the repository and may be used to upload the files to the __NGDAC__.  The script requires the following Perl non-core modules:
+ [Readonly](http://search.cpan.org/~roode/Readonly-1.03/Readonly.pm)
+ [Net::FTP](http://search.cpan.org/~shay/libnet-1.25/Net/FTP.pm)

__You must specify your credentials in the $USER and $PASS variables contained in the script__.  

## Dataset Status

Once one or more files have been successfully uploaded for the specified deployment, the [aggregation](https://github.com/ioos/ioosngdac/wiki/NGDAC-Architecture#data-assembly-center-architecture) process begins.  As there are multiple file syncing and aggregation processes going on, it will take some time for the data access end points on both the [ERDDAP](http://data.ioos.us/gliders/erddap/tabledap/index.html) and [THREDDS](http://data.ioos.us/gliders/thredds/catalog.html) servers to be created and populated.  The end-to-end processing pathway <b>currently takes 1 - 2 hrs</b>.  We are actively working on ways to decrease this time frame.

We've built a [dataset status](http://data.ioos.us/gliders/status/) page to provide administrators and users with the ability to track datasets through the end-to-end process.  The [home page](http://data.ioos.us/gliders/status/) displays a list of all data sets for which either/both the [ERDDAP](http://data.ioos.us/gliders/erddap/tabledap/index.html) and [THREDDS](http://data.ioos.us/gliders/thredds/catalog.html) are not yet available.  Please check this page before emailing the DAC administrators regarding data set availability.

## Dataset Archiving

Once a glider deployment is <b>completed</b>, the dataset is added to the [National Ocean Data Center's](http://www.nodc.noaa.gov/) national ocean archive.  <b>It is the responsibility of the individual data provider to mark the deployment as completed before it will be archived NODC</b>.  A deployment is marked as complete by checking the <b>Completed</b> checkbox on the individual deployment creation page.  Once this box has been checked, an [md5 checksum](http://en.wikipedia.org/wiki/MD5) is generated on the trajectory NetCDF file and the dataset is added to the <NODC> archive.

<b>The details of the NODC archiving process are still under development, so datasets are not currently archived by NODC.  We are working with NODC on this</b>.