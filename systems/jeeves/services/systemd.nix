{
  pkgs,
  self,
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
          ExecStart = "${pkgs.bash}/bin/bash ${../scripts/plex_permission.sh}";
        };
      };
      startup_validation = {
        requires = [ "network-online.target" ];
        after = [ "network-online.target" ];
        wantedBy = [ "multi-user.target" ];
        description = "validates startup";
        path = [ pkgs.zfs ];
        environment = {
          PYTHONPATH = "${self}/";
        };
        serviceConfig = {
          EnvironmentFile = "${vars.secrets}/services/server-validation";
          Type = "oneshot";
          ExecStart = "${pkgs.my_python}/bin/python -m python.tools.validate_system '${./validate_system.toml}'";
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
