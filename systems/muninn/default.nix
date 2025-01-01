{ inputs, pkgs, ... }:
{
  imports = [
    ../../users/gaming
    ../../users/richie
    ../../common/global
    ../../common/optional/desktop.nix
    ../../common/optional/steam.nix
    ../../common/optional/systemd-boot.nix
    ../../common/optional/update.nix
    ./hardware.nix
    inputs.nixos-hardware.nixosModules.framework-11th-gen-intel
  ];

  environment.systemPackages = with pkgs; [
    plex-media-player
  ];

  networking = {
    hostName = "muninn";
    hostId = "a43179c5";
    firewall.enable = true;
    networkmanager.enable = true;
  };

  hardware = {
    pulseaudio.enable = false;
    bluetooth = {
      enable = true;
      powerOnBoot = true;
    };
    firmware = [ pkgs.sof-firmware ];
  };

  security.rtkit.enable = true;

  services = {
    displayManager = {
      enable = true;
      autoLogin = {
        user = "gaming";
        enable = true;
      };
      defaultSession = "steam";
      # defaultSession = "plasma";
    };

    openssh.ports = [ 295 ];

    snapshot_manager.enable = true;

    zfs = {
      trim.enable = true;
      autoScrub.enable = true;
    };
  };

  system.stateVersion = "24.05";
}
