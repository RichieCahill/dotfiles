#!/bin/bash

# zpools

# media
sudo zpool create -o ashift=12 -O acltype=posixacl -O atime=off -O dnodesize=auto -O xattr=sa -O compression=zstd -m /zfs/media media mirror
sudo zpool add media -o ashift=12 special mirror

# storage
sudo zpool create -o ashift=12 -O acltype=posixacl -O atime=off -O dnodesize=auto -O xattr=sa -O compression=zstd -m /zfs/storage storage
sudo zpool add storage -o ashift=12 special mirror
sudo zpool add storage -o ashift=12 logs mirror

# scratch
sudo zpool create scratch -o ashift=12 -O acltype=posixacl -O atime=off -O dnodesize=auto -O xattr=sa -O compression=zstd -O encryption=aes-256-gcm -O keyformat=hex -O keylocation=file:///key -m /zfs/scratch

# media datasets
sudo zfs create -o compression=zstd-9 media/docker
sudo zfs create -o compression=zstd-9 -o sync=disabled media/github-runners
sudo zfs create -o copies=3 media/notes
sudo zfs create -o compression=zstd-9 media/plex
sudo zfs create -o compression=zstd-9 media/services
sudo zfs create -o compression=zstd-19 media/home_assistant
sudo zfs create -o exec=off media/share
sudo zfs create -o recordsize=16k -o primarycache=metadata -o mountpoint=/zfs/media/database/postgres media/postgres

# scratch datasets
sudo zfs create scratch/kafka -o mountpoint=/zfs/scratch/kafka -o recordsize=1M
sudo zfs create scratch/transmission -o mountpoint=/zfs/scratch/transmission -o recordsize=16k -o sync=disabled

# storage datasets
sudo zfs create -o recordsize=1M -o compression=zstd-19 storage/archive
sudo zfs create -o compression=zstd-19 storage/main
sudo zfs create -o recordsize=16K -o compression=zstd-19 -o copies=2 storage/photos
sudo zfs create -o recordsize=1M -o compression=zstd-19 storage/plex
sudo zfs create -o compression=zstd-19 -o copies=3 storage/secrets
sudo zfs create -o compression=zstd-19 storage/syncthing
sudo zfs create -o recordsize=1M -o compression=zstd-9 -o exec=off -o sync=disabled storage/qbitvpn
sudo zfs create -o recordsize=1M -o compression=zstd-9 -o exec=off -o sync=disabled storage/transmission
sudo zfs create -o recordsize=1M -o compression=zstd-19 storage/library
sudo zfs create -o recordsize=1M -o compression=zstd-19 -o sync=disabled storage/ollama
