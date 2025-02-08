{
  inputs,
  pkgs,
  lib,
  config,
  ...
}:
let
  cfg = config.services.snapshot_manager;
in
{
  options = {
    services.snapshot_manager = {
      enable = lib.mkOption {
        default = true;
        example = true;
        description = "Whether to enable k3s-net.";
        type = lib.types.bool;
      };
      path = lib.mkOption {
        type = lib.types.path;
        description = "Path that needs to be updated via git pull";
        default = ./snapshot_config.toml;
      };
    };
  };

  config = lib.mkIf cfg.enable {
    systemd = {
      services."snapshot_manager" = {
        description = "ZFS Snapshot Manager";
        requires = [ "zfs-import.target" ];
        after = [ "zfs-import.target" ];
        path = [ pkgs.zfs ];
        serviceConfig = {
          Type = "oneshot";
          ExecStart = "${inputs.system_tools.packages.x86_64-linux.default}/bin/snapshot_manager --config-file='${cfg.path}'";
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
  };
}
