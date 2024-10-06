#!/bin/bash

# zpools

sudo zpool create -o ashift=12 -O acltype=posixacl -O atime=off -O dnodesize=auto -O xattr=sa -O zstd -m /zfs/media media mirror
sudo zpool add media -o ashift=12 special mirror

sudo zpool create -o ashift=12 -O acltype=posixacl -O atime=off -O dnodesize=auto -O xattr=sa -O zstd -m /zfs/storage storage
sudo zpool add storage -o ashift=12 special mirror
sudo zpool add storage -o ashift=12 logs mirror

sudo zpool create -o ashift=12 -O acltype=posixacl -O atime=off -O dnodesize=auto -O xattr=sa -O zstd -m /zfs/torrenting torrenting

# media datasets
sudo zfs create -o compression=zstd-9 media/plex
sudo zfs create -o compression=zstd-9 media/docker
sudo zfs create -o exec=off media/mirror
sudo zfs create -o exec=off media/minio
sudo zfs create -o copies=3 media/notes
sudo zfs create -o recordsize=16k -o primarycache=metadata -o mountpoint=/zfs/media/database/postgres media/postgres
sudo zfs create -o recordsize=16k -o primarycache=metadata -o mountpoint=/zfs/media/database/photoprism_mariadb media/photoprism_mariadb

# storage datasets
sudo zfs create -o recordsize=16K -o compression=zstd-19 -o copies=2 storage/photos
sudo zfs create -o recordsize=1M -o compression=zstd-19 storage/archive

# torrenting datasets
sudo zfs create -o recordsize=16K -o exec=off -o sync=disabled torrenting/qbit
sudo zfs create -o recordsize=16K -o exec=off -o sync=disabled torrenting/qbitvpn
