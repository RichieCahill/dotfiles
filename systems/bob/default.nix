{
  inputs,
  ...
}:
{
  imports = [
    inputs.nixos-hardware.nixosModules.framework-13-7040-amd
    ../../users/richie
    ../common/global
    ../common/optional/desktop.nix
    ../common/optional/steam.nix
    ../common/optional/syncthing_base.nix
    ../common/optional/systemd-boot.nix
    ../common/optional/zerotier.nix
    ./hardware.nix
    ./nvidia.nix
  ];

  networking = {
    hostName = "bob";
    networkmanager.enable = true;
    hostId = "7c678a41";
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

    openssh.ports = [ 262 ];

    printing.enable = true;

    pipewire = {
      enable = true;
      alsa.enable = true;
      alsa.support32Bit = true;
      pulse.enable = true;
    };

    syncthing.settings.folders = {
      "notes" = {
        id = "l62ul-lpweo"; # cspell:disable-line
        path = "/home/richie/notes";
        devices = [
          "jeeves"
        ];
        fsWatcherEnabled = true;
      };
      "books" = {
        id = "6uppx-vadmy"; # cspell:disable-line
        path = "/home/richie/books";
        devices = [
          "phone"
          "jeeves"
        ];
        fsWatcherEnabled = true;
      };
      "important" = {
        id = "4ckma-gtshs"; # cspell:disable-line
        path = "/home/richie/important";
        devices = [
          "phone"
          "jeeves"
        ];
        fsWatcherEnabled = true;
      };
      "music" = {
        id = "vprc5-3azqc"; # cspell:disable-line
        path = "/home/richie/music";
        devices = [
          "ipad"
          "phone"
          "jeeves"
        ];
        fsWatcherEnabled = true;
      };
      "projects" = {
        id = "vyma6-lqqrz"; # cspell:disable-line
        path = "/home/richie/projects";
        devices = [
          "jeeves"
        ];
        fsWatcherEnabled = true;
      };
    };

    zfs = {
      trim.enable = true;
      autoScrub.enable = true;
    };
  };

  system.stateVersion = "24.05";
}
