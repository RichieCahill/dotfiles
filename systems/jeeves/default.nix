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
    ./home_assistant.nix
    ./networking.nix
    ./programs.nix
    ./services.nix
    ./syncthing.nix
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
      path = [ pkgs.zfs ];
      serviceConfig = {
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
