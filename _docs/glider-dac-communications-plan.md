---
title: Glider DAC Communications Plan
wikiPageName: Glider-DAC-Communications-Plan
keywords: IOOS, documentation
tags: [getting_started, about, overview]
toc: false
#search: exclude
#permalink: index.html
summary: These brief instructions will help you get started quickly with the IOOS Documentation Theme for Jekyll.
---

Assessing the current state of glider DAC documentation and coming up with a strategy for docs that is clear for data providers, program managers, and data consumers.

Currently we have the following URLs that contain some piece of the glider story.  What is current/accurate/relevant?  What is missing? What is out of date and in need of updating?  What is redundant or unnecessary and should be deleted?

# Data Flow and Distribution
1. Glider DAC landing page (<http://gliders.ioos.us>)- Purpose: Be the landing page for data providers to a) register deployments and b) check on the status of data files  (What else?  Is there more purpose to this page?)

# Technical Docs and Github Repos
1. Glider DAC Github Repo (<https://github.com/ioos/glider-dac>) - Purpose: maintain the code that creates/manages the <http://gliders.ioos.us> page.  Questions: Is this all?  Does this code also handle the entire back end data manipulation, FTP management, Error checking, compliance checking (TBD), THREDDS and ERDDAP management and catalog creation?  Where does this code fit in with the following diagram?

![DAC ARchitecture](https://raw.githubusercontent.com/kerfoot/ioosngdac/master/doco/IOOS-DAC-architecture.png)

1. Glider catalogs (<https://github.com/ioos/glider-dac-catalog>) - Purpose: Unclear.  The README states  "Catalogs for IOOS Glider DAC v2 <http://gliders.ioos.us>" but it hasn't been updated since Aug 28.
1. Other glider catalogs (https://github.com/ioos/glider_dac_thredds_catalog>) - Purpose: Unclear. README suggests that it is the repo of catalogs for the v1.0 DAC TDS.  Last updated 7 days ago by kwilcox (????)
  1. ACTION: Clarify the purpose of the above 2 repos, and merge/delete.  If there is a reason not to delete one then at least update the README to be accurate and more descriptive.  For example, the README on glider_dac_thredds_catalog still points to <https://github.com/IOOSProfilingGliders/Real-Time-File-Format/wiki>.

# Maps and Data Server Topmost Catalogs
More thought into this section...ran out of steam

1. THREDDS v1.0
1. THREDDS v2.0
1. ERDDAP v2.0
1. WAF with 2.0 ERDDAP metadata
1. WAF with 2.0 THREDDS metadata
1. Glider Asset Map on IOOS web site
1. Glider map on catalog

# Use Cases and Audiences
Thoughts on the various audiences to consider:

1. New data providers: where do we send them?  Is it sufficient to send them only to the topmost wiki page?  I assume the answer is <https://github.com/ioos/ioosngdac/> and if so then we should update the README to provide a little introduction and orientation to the new user.  
1. Data Provider: I want to check the status of the deployments that I think should be on the DAC.  Where do I go?  <http://gliders.ioos.us/>? <http://catalog.ioos.us/gliders>?, <http://www.ioos.noaa.gov/observing/observing_assets/glider_asset_map.html>? Glider DAC [ERDDAP](http://data.ioos.us/gliders/erddap/info/index.html?page=1&itemsPerPage=1000)?  Glider DAC [THREDDS](http://data.ioos.us/gliders/thredds/catalog.html)? Glider DAC metadata WAF <http://data.ioos.us/gliders/metadata-erddap/> or <http://data.ioos.us/gliders/metadata-thredds/>?
  1. ACTION: Create some sort of landing page for <http://data.ioos.us/gliders/> and <http://data.ioos.us>.  It can be temporary and basic but we don't want to leave people on an island.  If I reach a site like <http://data.ioos.us/gliders/>, my natural inclination is to traverse up the directory tree to see what is one level higher.  Consider the material on <gliders.ioos.us> and <catalog.ioos.us/gliders> as fodder for the possible merger.  Some whiteboarding is in order here I think.
1. Data Provider: Are my data on the GTS?  I realize there is no perfect answer.  What is our best answer?  [OSMC](http://osmc.noaa.gov/Monitor/OSMC/OSMC.html)? NDBC [Glider Page](http://www.ndbc.noaa.gov/gliders.php)?  

# Straw Man Recommendations
Given all of this, the following is a straw man for discussion.  I'm seeing a gradual merger of data management functions with catalog functions but I haven't thought it through completely. PLEASE NOTE: I'm not wed to the words below, I'm just trying to get a sense of the information we have, what we need, and how it might be organized.  Please contribute better ideas!

```
data.ioos.us/gliders (Main landing page for all things related to glider data.  I don't know how this should related to catalog.ioos.us/gliders.  We should discuss whether both are necessary.)  
 |
 +--> *Operators* (data.ioos.us/gliders/operators which is simply a migration of gliders.ioos.us)
    |
    +--> *Documentation* (data.ioos.us/gliders/operators/documentation that points to the relevant github repos/wikis such as github.com/ioos/ioosngdac/wiki Link to the SINGLE page for technical docs relevant to providers.  Please note, this wiki can easily be turned in to a web page residing at ioos.github.io/ioosngdac using tools like Pelican or Hugo.  See ioos.github.io/sos-guidelines for an example)  NOTE: The technical documentation at ioosngdac should refer to the  other github repos as well.
 +--> *Monitoring* (data.ioos.us/gliders/monitoring TBD stats and GTS tracking if possible.  Probably the most uncertain but lots of possiblities for integration of tools, esp those maps/summaries based on ERDDAP and developed by John K)
 +--> *Access* (data.ioos.us/gliders/access description of the various ways to get data and metadata including examples of using the ERDDAP/TDS)
    |
    +--> links to WAF, TDS, ERDDAP, Catalog and or other maps, CS/W queries of Geoportal, ultimately NODC Archive packages.
```
