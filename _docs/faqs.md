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


## Can I re-upload files to the DAC to incorporate more metadata based on compliance checker guidance?

Yes! There are typically 2 ways to update the metadata in your glider deployment. You could delete **ALL** of the existing netCDF files from the FTP server and then replace them with new ones.

OR...

The DAC ERDDAP server is set up to pull metadata from the most recently modified netCDF file. So you could simply update the latest file with the new/modified metadata and upload it. On the next rescan ERDDAP will pick up the changes and propagate them to the aggregate dataset.

Either way works.

## Can I submit variables other than the core CTD variables?

Yes! The DAC now accepts any science variables that have a valid [CF Standard Name](https://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html). Any ancillary variables (as specified in the variable attribute `ancillary_variables`) will also be ingested into ERDDAP.


## What is the current procedure for sending data to the Global Telecommunications System (GTS)?

The National Data Buoy Center harvests new profile observations from the [DAC's ERDDAP server](https://gliders.ioos.us/erddap/index.html) once per hour, encodes the profiles in to a modified drifting buoy BUFR format and releases the messages to the GTS.  The development of a glider specific BUFR format is currently being developed and finalized.
