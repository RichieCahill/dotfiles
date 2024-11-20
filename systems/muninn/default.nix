{ pkgs, ... }:
{


  imports = [
    ../../users/richie
    ../../users/gaming
    ../../common/global
    ../../common/optional/steam.nix
    ../../common/optional/systemd-boot.nix
    ./hardware.nix
  ];

  boot = {
    kernelPackages = pkgs.linuxPackages_zen;
    zfs.package = pkgs.zfs_unstable;
  };

  environment.loginShellInit = ''[[ "$(tty)" = "/dev/tty1" ]] && ${./gamescope.sh}'';

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
  };

  security.rtkit.enable = true;

  services = {
    getty = {
      # loginProgram = ./gamescope.sh;
      autologinUser = "gaming";
    };

    openssh.ports = [ 262 ];

    printing.enable = true;

    pipewire = {
      enable = true;
      alsa.enable = true;
      alsa.support32Bit = true;
      pulse.enable = true;
    };

    snapshot_manager.enable = true;

    zfs = {
      trim.enable = true;
      autoScrub.enable = true;
    };
  };

  system.stateVersion = "24.05";
}
