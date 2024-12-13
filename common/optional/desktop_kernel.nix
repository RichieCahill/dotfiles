{ pkgs, ... }:
{
  boot = {
    kernelPackages = pkgs.master.linuxPackages_6_12;
    zfs.package = pkgs.master.zfs;
  };
}
