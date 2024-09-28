#!/bin/bash

# media datasets
sudo zfs create -o compression=zstd-9 -o encryption=off -o atime=off media/plex
sudo zfs create -o compression=zstd-9 -o encryption=off -o atime=off media/docker
sudo zfs create -o encryption=off -o atime=off -o exec=off media/mirror
sudo zfs create -o encryption=off -o atime=off -o exec=off media/minio
sudo zfs create -o encryption=off -o atime=off -o copies=3 media/notes

# torrenting datasets
sudo zfs create -o recordsize=16K -o encryption=off -o atime=off -o exec=off -o sync=disabled torrenting/qbit
sudo zfs create -o recordsize=16K -o encryption=off -o atime=off -o exec=off -o sync=disabled torrenting/qbitvpn
