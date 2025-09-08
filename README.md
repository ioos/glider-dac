Glider DAC
==========
[![Build Status](https://travis-ci.org/ioos/glider-dac.svg?branch=master)](https://travis-ci.org/ioos/glider-dac)
[![Check Markdown links](https://github.com/ioos/glider-dac/actions/workflows/md-link-check.yml/badge.svg)](https://github.com/ioos/glider-dac/actions/workflows/md-link-check.yml)

This is the main repository for the IOOS Glider DAC site, scripts, and tools.

Detailed documentation on contact information, file format, user account registration, deployment registration and file submission can be found on the [IOOS National Glider DAC wiki](https://ioos.github.io/glider-dac/index.html).

Inquires should be sent to glider.dac.support@noaa.gov

## Development build

To create a development build, install Docker and Docker Compose.

Run `docker-compose up -d` to run the initial setup.

Glider DAC is driven by NetCDF data, so if you are not intending to populate a
development copy with your own glider data, you'll likely want to request
read-only S3 access for the NetCDF data and database contents without password
by emailing a request to glider.dac.support@noaa.gov and explaining your use case.

Once this is in place, optionally create a folder where you wish to sync data
as a bind mount for docker and then in the `.env` file, set the `DATA_VOLUME`
environment variable to match the local path of the data directory. If using a bind mount, ensure that the corresponding directories for the submission and served ERDDAP data
exist with the filesystem hierarchy.  By default in the configuration, these
are `submission` and `data/priv_erddap` by default.  Issuing the following command in shell will create the
necessary directories: <br > `mkdir -p /<DESTINATION_DATA_DIRECTORY>/submission /DESTINATION_DATA_DIRECTORY/data/priv_erddap` <br >

The default compose setup comes with a named Docker volume, so it is also an
option to copy directly to this mount using `docker cp` or moving the files to
the volume location reported by `docker volume inspect gliderdac_data_volume`. <br >

Create an empty file named `datasets.xml` in the project root directory `glider-dac` so that
ERDDAP can populate the datasets when running the job to add XML dataset entries
to this file. <br >

Next, comment out the line `- ./config.local.yml:/glider-dac/config.local.yml` in the docker-compose.yml file. Look under `volumes:` in the `glider-dac-providers-app:` services section. This step is necessary to setting up the correct configuration for the providers app. <br >

Then, run the `aws s3 sync` command to fetch the data, with `s3://ioosngdac/submission/`
as the source directory. It is recommended to fetch a subset of the data using the `--include` option.
Here, the command fetches NetCDF files with "202312" in the name, corresponding
to glider profiles which started in December 2023:
`
aws s3 sync s3://ioosngdac/submission/ <DESTINATION_DATA_DIRECTORY>/submission --exclude '*' --include '*202312*.nc'` <br >
`

While the data are downloading from the s3 bucket, copy one of the nightly database backups and restore it to the database:
```
mkdir backup_dir
cd backup_dir
aws s3 cp s3://ioosngdac/backups/2023-12-29-gliderdac-mongodb.tar.gz .
tar xf 2023-12-29-gliderdac-mongodb.tar.gz
docker cp mongo_dumps mongo:/data/
docker exec -w /data mongo sh -c "mongorestore mongo_dumps/dump && rm -rf mongo_dumps"
rm -rf mongo_dumps
```

Once these steps are run, you should be able to navigate to the development server
at http://localhost:5000 and view various deployments.

If desired, create a user with `docker exec -it glider-dac-providers-app python usertool.py set <username>`
to add a user and set the password.  If creating a user with the same name as one of the restored users in the database backup,
this will set the password and allow you to perform editing actions once logged in as the user through the application.
