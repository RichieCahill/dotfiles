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
      enable = lib.mkEnableOption "ZFS snapshot manager";
      path = lib.mkOption {
        type = lib.types.path;
        default = ./snapshot_config.toml;
        description = "Path to the snapshot_manager TOML config.";
      };
      EnvironmentFile = lib.mkOption {
        type = lib.types.nullOr (lib.types.coercedTo lib.types.path toString lib.types.str);
        default = null;
        description = ''
          Single environment file for the service (e.g. /etc/snapshot-manager/env).
          Use a leading "-" to ignore if missing (systemd feature).
        '';
      };
    };
  };

  config = lib.mkIf cfg.enable {
    systemd = {
      services.snapshot_manager = {
        description = "ZFS Snapshot Manager";
        requires = [ "zfs-import.target" ];
        after = [ "zfs-import.target" ];
        path = [ pkgs.zfs ];
        serviceConfig = {
          Type = "oneshot";
          ExecStart = "${
            inputs.system_tools.packages.${pkgs.system}.default
          }/bin/snapshot_manager ${lib.escapeShellArg cfg.path}";
        }
        // lib.optionalAttrs (cfg.EnvironmentFile != null) {
          EnvironmentFile = cfg.EnvironmentFile;
        };
      };
      timers.snapshot_manager = {
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
