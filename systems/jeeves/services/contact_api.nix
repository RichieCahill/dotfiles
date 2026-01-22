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
    description = "Contact Database API with Frontend";
    after = [
      "postgresql.service"
      "network.target"
    ];
    requires = [ "postgresql.service" ];
    wantedBy = [ "multi-user.target" ];
    path = [
      pkgs.nodejs
      pkgs.coreutils
      pkgs.bash
    ];

    environment = {
      PYTHONPATH = "${inputs.self}";
      POSTGRES_DB = "richie";
      POSTGRES_HOST = "/run/postgresql";
      POSTGRES_USER = "richie";
      POSTGRES_PORT = "5432";
      HOME = "/var/lib/contact-api";
    };

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.my_python}/bin/python -m python.api.main --host 192.168.90.40 --port 8069 --frontend-dir ${inputs.self}/frontend";
      StateDirectory = "contact-api";
      Restart = "on-failure";
      RestartSec = "5s";
      StandardOutput = "journal";
      StandardError = "journal";
      # Security hardening
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
