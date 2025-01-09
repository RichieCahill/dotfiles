{ inputs, ... }:
{
  imports = [
    ../../users/richie
    ../../common/global
    ../../common/optional/desktop.nix
    ../../common/optional/docker.nix
    ../../common/optional/steam.nix
    ../../common/optional/syncthing_base.nix
    ../../common/optional/systemd-boot.nix
    ../../common/optional/yubikey.nix
    ../../common/optional/zerotier.nix
    ./hardware.nix
    ./syncthing.nix
    inputs.nixos-hardware.nixosModules.framework-13-7040-amd
  ];

  networking = {
    hostName = "rhapsody-in-green";
    hostId = "6404140d";
    firewall.enable = true;
    networkmanager.enable = true;
  };

  hardware = {
    bluetooth = {
      enable = true;
      powerOnBoot = true;
    };
  };

  security.rtkit.enable = true;

  services = {

    openssh.ports = [ 922 ];

    snapshot_manager.enable = true;

    zfs = {
      trim.enable = true;
      autoScrub.enable = true;
    };
  };

  system.stateVersion = "24.05";
}
