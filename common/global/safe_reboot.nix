{
  config,
  inputs,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.safe_reboot;
  python_command =
    lib.escapeShellArgs (
      [
        "${pkgs.my_python}/bin/python"
        "-m"
        "python.tools.safe_reboot"
      ]
      ++ lib.optionals (cfg.drivePath != null) [ cfg.drivePath ]
      ++ [
        "--dataset-prefix"
        cfg.datasetPrefix
        "--check-only"
      ]
    );
in
{
  options.services.safe_reboot = {
    enable = lib.mkEnableOption "Safe reboot dataset/drive validation";
    datasetPrefix = lib.mkOption {
      type = lib.types.str;
      default = "root_pool/";
      description = "Dataset prefix that must have exec enabled before rebooting.";
    };
    drivePath = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "Drive path that must exist before rebooting. Set to null to skip.";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.safe-reboot-check = {
      description = "Safe reboot validation";
      before = [ "systemd-reboot.service" ];
      wantedBy = [ "reboot.target" ];
      partOf = [ "reboot.target" ];
      path = [ pkgs.zfs ];
      environment = {
        PYTHONPATH = "${inputs.self}/";
      };
      serviceConfig = {
        Type = "oneshot";
        ExecStart = python_command;
      };
    };
  };
}
