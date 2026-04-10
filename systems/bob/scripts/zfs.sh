#!/bin/bash

# zpools

# storage
sudo zpool create -f -o ashift=12 -O acltype=posixacl -O atime=off -O dnodesize=auto -O xattr=sa -O compression=zstd -m /zfs/storage storage mirror
sudo zpool create -o ashift=12 -O acltype=posixacl -O atime=off -O dnodesize=auto -O xattr=sa -O compression=zstd -m /zfs/storage storage


# storage datasets
sudo zfs create storage/models -o recordsize=1M
