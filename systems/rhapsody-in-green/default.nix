{ inputs, ... }:
{
  imports = [
    ../../users/richie
    ../common/global
    ../common/optional/desktop.nix
    ../common/optional/syncthing_base.nix
    ../common/optional/systemd-boot.nix
    ../common/optional/yubikey.nix
    ../common/optional/zerotier.nix
    ./hardware.nix
    ./syncthing.nix
    inputs.nixos-hardware.nixosModules.framework-13-7040-amd
  ];

  networking = {
    hostName = "rhapsody-in-green";
    networkmanager.enable = true;
    hostId = "9b68eb32";
  };

  hardware = {
    pulseaudio.enable = false;
    bluetooth = {
      enable = true;
      powerOnBoot = true;
    };
  };

  security.rtkit.enable = true;

  services = {

    displayManager.sddm.enable = true;

    openssh.ports = [ 922 ];

    printing.enable = true;

    pipewire = {
      enable = true;
      alsa.enable = true;
      alsa.support32Bit = true;
      pulse.enable = true;
    };

    zfs = {
      trim.enable = true;
      autoScrub.enable = true;
    };
  };

  system.stateVersion = "24.05";
}