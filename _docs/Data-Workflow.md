# NDBC Glider Data Monitoring and GTS

One function of the Glider DAC is to coordinate with the NWS' National Data Buoy Center to distribute real time glider data on the WMO Global Telecommuncations System (GTS) for use by operational modeling centers such as NCEP and the U.S. Navy (NAVO).  However, the average public user does not have visibility into the GTS data stream and has no way of determining if their glider data is in fact distributed to the GTS.  Currently the Glider DAC is also unable to monitor the GTS data stream directly.  There are however two sites that can give some insight into the GTS status.  

## NDBC Glider Page
Active and historical glider deployments are posted to an NDBC [glider page](http://www.ndbc.noaa.gov/gliders.php).  These questions and answers from NDBC clarify the information on the glider page specific information and GTS.  

1. **What constitutes "active?"  Right now, 11 gliders are in the active column, but are they all going to GTS or what makes them active?** 
If a glider is shown as active, it is presently deployed and making data available to NDBC for processing.  This does not guarantee that data are released to the GTS.  Data may post on the website even if it does not meet requirements for release to the GTS.  Right now all gliders shown as active are being released to the GTS
1. **Do they transition to historical as soon as they are recovered or is there a different mechanism to transition them?**             
A glider is no longer be classified as active if new data has not been available for five days.  This is automatically done by the web processing software.

## The Observing System Monitoring Center (OSMC)
[OSMC](www.osmc.info) is a monitoring tool that attempts to harvest and track all ocean observations on the GTS.  This tool is comprehensive but not perfect so if discrepencies are found we encourage users to contact OSMC directly OSMC.Webmaster-AT-noaa-DOT-gov. 

1. **It doesn't appear that everything in the active or historical columns goes to OSMC, so what does OSMC track?**
All glider data that we release to the GTS should be in OSMC.  Be sure to search the OSMC using the 7 digit WMO ID if the data were released in BUFR.  Our website only shows the last 5 digits of a 7 digit ID since the website processing code was designed to only accept IDs with 5 digits.  You can go to a glider's home page to find the full 7 digit ID.