#!/usr/bin/env bash

# BWA (2018-08-28) replaced old version with stale lock implementation
#                  with flock instead
lockfile=/tmp/deployment_sync
exec 500>"$lockfile"

if ! flock -n 500; then
    echo 'Lock already acquired for sync' 1>&2
    exit 1
else
    # Give the qartod process a chance to sleep
        sleep 5
    # BWA (2019-06-10): Remove --delete as it can be dangerous if the
    #                   /data/submission directory fails to mount
    # (2021-10-13) basic check to see if any folders are even present
    submission_subfolders=(/data/submission/*)
    if [[ "${#submission_subfolders[@]}" -gt 0 ]]; then
        # (2021-10-13) ensure dataset.xml isn't clobbered upon rsync --delete
        # TODO: remove path hardcoding
        rsync -avu --delete --chmod ug+rwX,o+rX --exclude dataset.xml --exclude 'navoceano/ng*/*.nc' /data/submission/ /data/data/priv_erddap/ >> /var/log/gliderdac/rsync.log 2>&1
    else
        echo 'Submission folder (/data/submission) appears to contain no subfolders, aborting' >&2
    fi
fi
