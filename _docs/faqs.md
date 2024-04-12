---
title: Frequently Asked Questions
wikiPageName: FAQs
keywords: IOOS, documentation
tags: [getting_started, about, overview]
toc: false
#search: exclude
#permalink: index.html
summary: A list of frequently asked questions
---


- [Can I re-upload files to the DAC to incorporate more metadata based on compliance checker guidance?](#can-i-re-upload-files-to-the-dac-to-incorporate-more-metadata-based-on-compliance-checker-guidance)
- [Can I submit variables other than the core CTD variables?](#can-i-submit-variables-other-than-the-core-ctd-variables)
- [What is the current procedure for sending data to the Global Telecommunications System (GTS)?](#what-is-the-current-procedure-for-sending-data-to-the-global-telecommunications-system-gts)
- [What criteria are used by NDBC to determine whether a profile(s) is released to GTS?](#what-criteria-are-used-by-ndbc-to-determine-whether-a-profile-is-released-to-gts)

## Can I re-upload files to the DAC to incorporate more metadata based on compliance checker guidance?

Yes! There are typically 2 ways to update the metadata in your glider deployment. You could delete **ALL** of the existing netCDF files from the FTP server and then replace them with new ones.

OR...

The DAC ERDDAP server is set up to pull metadata from the most recently modified netCDF file. So you could simply update the latest file with the new/modified metadata and upload it. On the next rescan ERDDAP will pick up the changes and propagate them to the aggregate dataset.

Either way works.

## Can I submit variables other than the core CTD variables?

Yes! The DAC now accepts any science variables that have a valid [CF Standard Name](https://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html). Any ancillary variables (as specified in the variable attribute `ancillary_variables`) will also be ingested into ERDDAP.


## What is the current procedure for sending data to the Global Telecommunications System (GTS)?

The National Data Buoy Center harvests new profile observations from the [DAC's ERDDAP server](https://gliders.ioos.us/erddap/index.html) once per hour, encodes the profiles in to a modified drifting buoy BUFR format and releases the messages to the GTS.  The development of a glider specific BUFR format is currently being developed and finalized.

## What criteria are used by NDBC to determine whether a profile is released to GTS?

The following 3 criteria must be true in order for a profile to be released to GTS:

1. The platform_meta variable must contain a __wmo_id__ attribute with a valid (7 digit) wmo id. If this attribute is missing or the ID is invalid, then the data set is not released to GTS.
2. The global __gts_ingest flag__ (default=True) must be set to True. If explicitly set to False, the data set is not released to GTS. We assume that, unless the data provider explicitly says they don’t want the data released to GTS, then the default is to send it. This is implemented both on the DAC and the NDBC side (default __gts_ingest=True__).
3. The profile must contain a minimum of 5 depth records to be considered a valid vertical profile.
