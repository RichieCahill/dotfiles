{ pkgs, ... }:
{
  boot = {
    kernelPackages = pkgs.linuxPackages_6_11;
    zfs.package = pkgs.zfs_unstable;
  };
}
