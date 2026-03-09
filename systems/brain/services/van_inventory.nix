{
  pkgs,
  inputs,
  ...
}:
{
  networking.firewall.allowedTCPPorts = [ 8001 ];

  users.users.vaninventory = {
    isSystemUser = true;
    group = "vaninventory";
  };
  users.groups.vaninventory = { };

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
      VAN_INVENTORY_DB = "vaninventory";
      VAN_INVENTORY_USER = "vaninventory";
      VAN_INVENTORY_HOST = "/run/postgresql";
      VAN_INVENTORY_PORT = "5432";
    };

    serviceConfig = {
      Type = "simple";
      User = "van-inventory";
      Group = "van-inventory";
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
