{ pkgs, ... }:
{
  boot = {
    kernelPackages = pkgs.linuxPackages_6_12;
    zfs.package = pkgs.zfs;
  };
}
