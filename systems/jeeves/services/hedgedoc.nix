{
  services.hedgedoc = {
    enable = true;
    settings = {
      host = "0.0.0.0";
      port = 3000;
      domain = "192.168.90.40";
      urlAddPort = true;
      protocolUseSSL = false;
      db = {
        dialect = "postgres";
        database = "hedgedoc";
        username = "hedgedoc";
        host = "/run/postgresql";
      };
    };
  };
  networking.firewall.allowedTCPPorts = [ 3000 ];

  systemd.services.hedgedoc = {
    after = [ "postgresql.service" ];
    requires = [ "postgresql.service" ];
  };
}
