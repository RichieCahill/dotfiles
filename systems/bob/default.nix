{ inputs, pkgs, ... }:
{
  imports = [
    "${inputs.self}/users/richie"
    "${inputs.self}/users/math"
    "${inputs.self}/common/global"
    "${inputs.self}/common/optional/docker.nix"
    "${inputs.self}/common/optional/scanner.nix"
    "${inputs.self}/common/optional/steam.nix"
    "${inputs.self}/common/optional/syncthing_base.nix"
    "${inputs.self}/common/optional/systemd-boot.nix"
    "${inputs.self}/common/optional/update.nix"
    "${inputs.self}/common/optional/yubikey.nix"
    "${inputs.self}/common/optional/zerotier.nix"
    "${inputs.self}/common/optional/nvidia.nix"
    ./hardware.nix
    ./syncthing.nix
    ./llms.nix
  ];

  boot = {
    kernelPackages = pkgs.linuxPackages_6_18;
    zfs.package = pkgs.zfs_2_4;
  };

  networking = {
    hostName = "bob";
    hostId = "7c678a41";
    firewall.enable = true;
    networkmanager.enable = true;
  };

  services = {
    openssh.ports = [ 262 ];

    snapshot_manager.path = ./snapshot_config.toml;
  };

  system.stateVersion = "24.05";
}
