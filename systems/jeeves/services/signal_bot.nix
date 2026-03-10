{
  pkgs,
  inputs,
  ...
}:
let
  vars = import ../vars.nix;
in
{
  users = {
    users.signalbot = {
      isSystemUser = true;
      group = "signalbot";
    };
    groups.signalbot = { };
  };

  systemd.services.signal-bot = {
    description = "Signal command and control bot";
    after = [
      "network.target"
      "podman-signal_cli_rest_api.service"
    ];
    wants = [ "podman-signal_cli_rest_api.service" ];
    wantedBy = [ "multi-user.target" ];

    environment = {
      PYTHONPATH = "${inputs.self}";
    };

    serviceConfig = {
      Type = "simple";
      User = "signalbot";
      Group = "signalbot";
      EnvironmentFile = "${vars.secrets}/services/signal-bot";
      ExecStart = "${pkgs.my_python}/bin/python -m python.signal_bot.main";
      StateDirectory = "signal-bot";
      Restart = "on-failure";
      RestartSec = "10s";
      StandardOutput = "journal";
      StandardError = "journal";
      NoNewPrivileges = true;
      ProtectSystem = "strict";
      ProtectHome = "read-only";
      PrivateTmp = true;
      ReadWritePaths = [ "/var/lib/signal-bot" ];
      ReadOnlyPaths = [
        "${inputs.self}"
      ];
    };
  };
}
