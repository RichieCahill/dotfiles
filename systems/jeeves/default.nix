{ inputs, pkgs, ... }:
let
  vars = import ./vars.nix;
in
{
  imports = [
    ../../users/richie
    ../common/global
    ../common/optional/ssh_decrypt.nix
    ../common/optional/syncthing_base.nix
    ../common/optional/systemd-boot.nix
    ../common/optional/zerotier.nix
    ./arch_mirror.nix
    ./docker
    ./hardware.nix
    ./networking.nix
    ./programs.nix
    ./services.nix
  ];

  boot.zfs.extraPools = [
    "media"
    "storage"
    "torrenting"
  ];

  services = {
    openssh.ports = [ 629 ];

    plex = {
      enable = true;
      dataDir = vars.media_plex;
    };

    smartd.enable = true;

    sysstat.enable = true;

    syncthing.guiAddress = "192.168.90.40:8384";
    syncthing.settings.folders = {
      "notes" = {
        id = "l62ul-lpweo"; # cspell:disable-line
        path = vars.media_notes;
        devices = [
          "bob"
        ];
        fsWatcherEnabled = true;
      };
      "books" = {
        id = "6uppx-vadmy"; # cspell:disable-line
        path = "${vars.storage_syncthing}/books";
        devices = [
          "bob"
          "phone"
        ];
        fsWatcherEnabled = true;
      };
      "important" = {
        id = "4ckma-gtshs"; # cspell:disable-line
        path = "${vars.storage_syncthing}/important";
        devices = [
          "bob"
          "phone"
        ];
        fsWatcherEnabled = true;
      };
      "music" = {
        id = "vprc5-3azqc"; # cspell:disable-line
        path = "${vars.storage_syncthing}/music";
        devices = [
          "bob"
          "ipad"
          "phone"
        ];
        fsWatcherEnabled = true;
      };
      "projects" = {
        id = "vyma6-lqqrz"; # cspell:disable-line
        path = "${vars.storage_syncthing}/projects";
        devices = [
          "bob"
        ];
        fsWatcherEnabled = true;
      };
    };

    zfs = {
      trim.enable = true;
      autoScrub.enable = true;
    };
  };
  systemd = {
    services."snapshot_manager" = {
      description = "ZFS Snapshot Manager";
      requires = [ "zfs-import.target" ];
      after = [ "zfs-import.target" ];
      serviceConfig = {
        Environment = "ZFS_BIN=${pkgs.zfs}/bin/zfs";
        Type = "oneshot";
        ExecStart = "${inputs.system_tools.packages.x86_64-linux.default}/bin/snapshot_manager --config-file='${./snapshot_config.toml}'";
      };
    };
    timers."snapshot_manager" = {
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnBootSec = "15m";
        OnUnitActiveSec = "15m";
        Unit = "snapshot_manager.service";
      };
    };
  };


  system.stateVersion = "24.05";
}
