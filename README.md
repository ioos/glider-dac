Glider DAC
==========
[![Build Status](https://travis-ci.org/ioos/glider-dac.svg?branch=master)](https://travis-ci.org/ioos/glider-dac)
[![Check Markdown links](https://github.com/ioos/glider-dac/actions/workflows/md-link-check.yml/badge.svg)](https://github.com/ioos/glider-dac/actions/workflows/md-link-check.yml)

This is the main repository for the IOOS Glider DAC site, scripts, and tools.

## Install Notes

The `bsddb3` python package requires Berkeley DB installed. If using OSX, this can be done with `brew install berkeley-db`, but in order to install `bsddb3`, you'll need to execute the following (update for your current installed version):

```
export BERKELEYDB_INCDIR=/usr/local/Cellar/berkeley-db/5.3.21/include
export BERKELEYDB_LIBDIR=/usr/local/Cellar/berkeley-db/5.3.21/lib
export BERKELEYDB_DIR=/usr/local/Cellar/berkeley-db/5.3.21

pip install -r requirements.txt
```
## Updating the mongo schema
1. Add the attribute to the appropriate model (e.g. glider_dac/models/deployment.py)
1. Update `glider-dac/migrations/migration.py`
1. Run `glider-dac/migrations/migration.py`.
