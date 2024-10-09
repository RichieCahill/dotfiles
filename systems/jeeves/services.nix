{
  inputs,
  pkgs,
  ...
}:
let
  vars = import ../vars.nix;
in
{
  systemd = {
    services = {
      plex_permission = {
        description = "maintains /zfs/storage/plex permissions";
        serviceConfig = {
          Type = "oneshot";
          ExecStart = "${pkgs.bash}/bin/bash ${./scripts/plex_permission.sh}";
        };
      };
      startup_validation = {
        requires = [ "network-online.target" ];
        after = [ "network-online.target" ];
        wantedBy = [ "multi-user.target" ];
        description = "validates startup";
        path = [ pkgs.zfs ];
        serviceConfig = {
          EnvironmentFile = "${vars.storage_secrets}/services/server-validation";
          Type = "oneshot";
          ExecStart = "${inputs.system_tools.packages.x86_64-linux.default}/bin/validate_jeeves";
        };
      };
    };
    timers = {
      plex_permission = {
        wantedBy = [ "timers.target" ];
        timerConfig = {
          OnBootSec = "1h";
          OnCalendar = "daily 03:00";
          Unit = "plex_permission.service";
        };
      };
      startup_validation = {
        wantedBy = [ "timers.target" ];
        timerConfig = {
          OnBootSec = "10min";
          Unit = "startup_validation.service";
        };
      };
    };
  };
}
