#!/bin/bash

# zpools

# media
sudo zpool create -o ashift=12 -O acltype=posixacl -O atime=off -O dnodesize=auto -O xattr=sa -O zstd -m /zfs/media media mirror
sudo zpool add media -o ashift=12 special mirror

# storage
sudo zpool create -o ashift=12 -O acltype=posixacl -O atime=off -O dnodesize=auto -O xattr=sa -O zstd -m /zfs/storage storage
sudo zpool add storage -o ashift=12 special mirror
sudo zpool add storage -o ashift=12 logs mirror

# torrenting
sudo zpool create -o ashift=12 -O acltype=posixacl -O atime=off -O dnodesize=auto -O xattr=sa -O zstd -m /zfs/torrenting torrenting
sudo zpool add torrenting -o ashift=12 special

# media datasets
sudo zfs create -o compression=zstd-9 media/docker
sudo zfs create -o recordsize=1M -o compression=zstd-19 media/library
sudo zfs create -o exec=off media/minio
sudo zfs create -o exec=off media/mirror
sudo zfs create -o copies=3 media/notes
sudo zfs create -o recordsize=16k -o primarycache=metadata -o mountpoint=/zfs/media/database/photoprism_mariadb media/photoprism_mariadb
sudo zfs create -o compression=zstd-9 media/plex
sudo zfs create -o recordsize=16k -o primarycache=metadata -o mountpoint=/zfs/media/database/postgres media/postgres

# storage datasets
sudo zfs create -o recordsize=1M -o compression=zstd-19 storage/archive
sudo zfs create -o compression=zstd-19 storage/main
sudo zfs create -o recordsize=16K -o compression=zstd-19 -o copies=2 storage/photos
sudo zfs create -o recordsize=1M -o compression=zstd-19 storage/plex
sudo zfs create -o compression=zstd-19 -o copies=3 storage/secrets
sudo zfs create -o compression=zstd-19 storage/syncthing

# torrenting datasets
sudo zfs create -o recordsize=16K -o exec=off -o sync=disabled torrenting/qbit
sudo zfs create -o recordsize=16K -o exec=off -o sync=disabled torrenting/qbitvpn
