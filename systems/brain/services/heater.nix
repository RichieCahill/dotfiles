{
  pkgs,
  inputs,
  ...
}:
{
  networking.firewall.allowedTCPPorts = [ 8124 ];

  systemd.services.heater-api = {
    description = "Tuya Heater Control API";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];

    environment = {
      PYTHONPATH = "${inputs.self}/";
    };

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.my_python}/bin/python -m python.heater.main --host 0.0.0.0 --port 8124";
      EnvironmentFile = "/etc/heater.env";
      Restart = "on-failure";
      RestartSec = "5s";
      StandardOutput = "journal";
      StandardError = "journal";
      NoNewPrivileges = true;
      ProtectSystem = "strict";
      ProtectHome = "read-only";
      PrivateTmp = true;
      ReadOnlyPaths = [ "${inputs.self}" ];
    };
  };
}
