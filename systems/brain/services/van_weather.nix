{
  pkgs,
  inputs,
  ...
}:
{
  systemd.services.van-weather = {
    description = "Van Weather Service";
    after = [ "network.target" "home-assistant.service" ];
    requires = [ "home-assistant.service" ];
    wantedBy = [ "multi-user.target" ];

    environment = {
      PYTHONPATH = "${inputs.self}/";
    };

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.my_python}/bin/python -m python.van_weather.main";
      EnvironmentFile = "/etc/van_weather.env";
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
