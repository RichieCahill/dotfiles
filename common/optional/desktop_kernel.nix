{ lib, pkgs, ... }:
{
  boot = {
    kernelPackages = lib.mkDefault pkgs.linuxPackages_zen;
    zfs.package = pkgs.zfs_unstable;
  };
}
