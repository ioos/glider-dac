Glider DAC
==========

### Install Notes

The `bsddb3` python package requires Berkeley DB installed. If using OSX, this can be done with `brew install berkeley-db`, but in order to install `bsddb3`, you'll need to execute the following (update for your current installed version):

```
export BERKELEYDB_INCDIR=/usr/local/Cellar/berkeley-db/5.3.21/include
export BERKELEYDB_LIBDIR=/usr/local/Cellar/berkeley-db/5.3.21/lib
export BERKELEYDB_DIR=/usr/local/Cellar/berkeley-db/5.3.21

pip install -r requirements.txt
```

