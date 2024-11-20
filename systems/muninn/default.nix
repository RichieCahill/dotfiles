{ inputs, ... }:
{


  imports = [
    ../../users/gaming
    ../../users/richie
    ../../common/global
    ../../common/optional/desktop_kernel.nix
    ../../common/optional/steam.nix
    ../../common/optional/systemd-boot.nix
    ./hardware.nix
    inputs.nixos-hardware.nixosModules.framework-11th-gen-intel
  ];

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
    getty.autologinUser = "gaming";

    openssh.ports = [ 295 ];

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
