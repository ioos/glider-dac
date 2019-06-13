---
title: Data Backup and Recovery
wikiPageName: Data-Backup-and-Recovery
keywords: IOOS, documentation
tags: [getting_started, about, overview]
toc: false
#search: exclude
#permalink: index.html
summary:  These brief instructions will help you get started quickly with the data backup and recovery processes.
---

## Data Backup

The Glider DAC v.2 has an automated backup script, run weekly by cron.  The cronjob is run under the "Glider" User.  The backup is stored in a bucket on Amazon S3.

IOOS NGDAC makes daily backups of the entire data file system to Amazon Simple Storage Service (S3). Every run the backup system checks the [Unix mtime](http://linux.die.net/man/2/stat) and compares that to the metadata in S3. If the mtime is different (regardless of newer or older) the script writes the local content to S3. We store several fields of metadata to ensure proper recovery in the event of failure:

 - Username
 - File Permissions
 - MD5 Sum



## Data Recovery

To recover the Glider DAC data, the awscli module must be used.  To install, run:

**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`    pip install awscli`**

After installing, the awscli must be configured.  Edit the config file located at ~/.aws/config to resemble the example below.

```
    [default]
    aws_access_key_id = **YOUR PERSONAL AWS ACCESS KEY**
    aws_secret_access_key = **YOUR PERSONAL SECRET AWS ACCESS KEY**
    output = text
    region = us-east-1
```

Once configured, the restore can be executed by running the following command:

**&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`    awscli s3 sync s3://ioosglidersbackupsv2  /location/to/restore`**

As of right now, the location to restore would be '/', however if the data root directory changes, so would this command.
