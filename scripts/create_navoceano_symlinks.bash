#!/bin/bash

# Make symlinks for created navo deployment directories which might
# not have symlinks yet.
shopt -s nullglob
navo_dir=/data/data/priv_erddap/navoceano
cd "$navo_dir" || exit

for dest_dir in ng*; do
    glider_name="${dest_dir%%-*}"
    for source_file in "hurricanes-20230601T0000/$glider_name"*.nc; do
        no_dir="${source_file#*/}"
        no_z="${no_dir/%Z.nc/.nc}"
        symlink_dest="$dest_dir/${no_z/_/-}"
        if [[ ! -L "$symlink_dest" ]]; then
            ln -s "$navo_dir/$source_file" "$symlink_dest"
        fi
    done
done
