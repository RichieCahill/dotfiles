{
  pkgs,
  inputs,
  ...
}:
{
  networking.firewall.allowedTCPPorts = [ 8001 ];

  users.users.van_inventory = {
    isSystemAccount = true;
    group = "van_inventory";
  };
  users.groups.van_inventory = { };

  systemd.services.van_inventory = {
    description = "Van Inventory API";
    after = [
      "network.target"
      "postgresql.service"
    ];
    requires = [ "postgresql.service" ];
    wantedBy = [ "multi-user.target" ];

    environment = {
      PYTHONPATH = "${inputs.self}/";
      VAN_INVENTORY_DB = "van_inventory";
      VAN_INVENTORY_USER = "van_inventory";
    };

    serviceConfig = {
      Type = "simple";
      User = "van_inventory";
      Group = "van_inventory";
      ExecStart = "${pkgs.my_python}/bin/python -m python.van_inventory.main --host 0.0.0.0 --port 8001";
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
