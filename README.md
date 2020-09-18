Glider DAC
==========

This is the main repository for the IOOS Glider DAC site, scripts, and tools

Please do not file issues here,  all GliderDAC related issues should be filed in the [IOOS National Glider Data Assembly Center (V2)](OOS National Glider Data Assembly Center (V2)) repository.

### Install Notes

The `bsddb3` python package requires Berkeley DB installed. If using OSX, this can be done with `brew install berkeley-db`, but in order to install `bsddb3`, you'll need to execute the following (update for your current installed version):

```
export BERKELEYDB_INCDIR=/usr/local/Cellar/berkeley-db/5.3.21/include
export BERKELEYDB_LIBDIR=/usr/local/Cellar/berkeley-db/5.3.21/lib
export BERKELEYDB_DIR=/usr/local/Cellar/berkeley-db/5.3.21

pip install -r requirements.txt
```
## Updating the mongo schema
1) Add the attribute to the appropriate model (e.g. glider_dac/models/deployment.py)
2) Update `glider-dac/migrations/migration.py`
3) Run `glider-dac/migrations/migration.py`.
