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
sudo zfs create media/secure -o encryption=aes-256-gcm -o keyformat=hex -o keylocation=file:///root/zfs.key
sudo zfs create media/secure/docker -o compression=zstd-9
sudo zfs create media/secure/github-runners -o compression=zstd-9 -o sync=disabled
sudo zfs create media/secure/home_assistant -o compression=zstd-19
sudo zfs create media/secure/notes -o copies=2
sudo zfs create media/secure/postgres -o recordsize=16k -o primarycache=metadata
sudo zfs create media/secure/services -o compression=zstd-9
sudo zfs create media/secure/share -o mountpoint=/zfs/media/share -o exec=off

# scratch datasets
sudo zfs create scratch/kafka -o mountpoint=/zfs/scratch/kafka -o recordsize=1M
sudo zfs create scratch/transmission -o mountpoint=/zfs/scratch/transmission -o recordsize=16k -o sync=disabled

# storage datasets
sudo zfs create storage/ollama -o recordsize=1M -o compression=zstd-19 -o sync=disabled
sudo zfs create storage/secure -o encryption=aes-256-gcm -o keyformat=hex -o keylocation=file:///root/zfs.key
sudo zfs create storage/secure/archive -o recordsize=1M -o compression=zstd-19
sudo zfs create storage/secure/library -o recordsize=1M -o compression=zstd-19
sudo zfs create storage/secure/main -o compression=zstd-19
sudo zfs create storage/secure/photos -o recordsize=16K -o compression=zstd-19 -o copies=2
sudo zfs create storage/secure/plex -o recordsize=1M -o compression=zstd-19
sudo zfs create storage/secure/secrets -o compression=zstd-19 -o copies=3
sudo zfs create storage/secure/syncthing -o compression=zstd-19
sudo zfs create storage/secure/transmission -o recordsize=1M -o compression=zstd-9 -o exec=off -o sync=disabled
