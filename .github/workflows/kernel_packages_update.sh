#!/bin/bash

# Update ZFS package to match the latest supported Linux kernel version

echo "geting latest ZFS version"
raw_zfs_max_kernel_version=$(curl -s https://raw.githubusercontent.com/openzfs/zfs/master/META | grep Linux-Maximum | cut -d" " -f2)

zfs_max_kernel_version="${raw_zfs_max_kernel_version//./_}"

echo "geting latest ZFS version"


if grep "linuxPackages_$zfs_max_kernel_version" systems/common/global/default.nix; then
    echo "No changes needed"
    exit 0
fi

sed -i "s/linuxPackages_6_[0-9]\+/linuxPackages_$zfs_max_kernel_version/" systems/common/global/default.nix

# Commit the changes
git config user.name "GitHub Actions Bot"
git config user.email "<>"
git add systems/common/global/default.nix
git commit -m "Update Linux kernel and ZFS packages"
