{
  pkgs,
  inputs,
  ...
}:
{
  networking.firewall.allowedTCPPorts = [
    8069
  ];
  systemd.services.contact-api = {
    description = "Contact Database API";
    after = [
      "postgresql.service"
      "network.target"
    ];
    requires = [ "postgresql.service" ];
    wantedBy = [ "multi-user.target" ];

    environment = {
      PYTHONPATH = "${inputs.self}";
      POSTGRES_DB = "richie";
      POSTGRES_HOST = "/run/postgresql";
      POSTGRES_USER = "richie";
      POSTGRES_PORT = "5432";
    };

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.my_python}/bin/python -m python.api.main --host 192.168.90.40 --port 8069";
      Restart = "on-failure";
      RestartSec = "5s";
      StandardOutput = "journal";
      StandardError = "journal";
      NoNewPrivileges = true;
      ProtectSystem = "strict";
      ProtectHome = "read-only";
      PrivateTmp = true;
      ReadOnlyPaths = [
        "${inputs.self}"
      ];
    };
  };
}
