{
  pkgs,
  inputs,
  ...
}:
{
  systemd.services.agent-logger = {
    description = "Unified agent logger";
    after = [ "local-fs.target" ];
    wantedBy = [ "multi-user.target" ];

    environment = {
      AGENT_LOG_DB = "/var/lib/agent-logger/agent_log.sqlite";
      HOME = "/home/richie";
      PYTHONPATH = "${inputs.self}";
    };

    serviceConfig = {
      Type = "simple";
      User = "richie";
      WorkingDirectory = "/home/richie";
      ExecStart = "${pkgs.my_python}/bin/python -m python.agent_logger.main";
      StateDirectory = "agent-logger";
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
