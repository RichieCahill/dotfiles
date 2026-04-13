{
  users.users.haproxy.extraGroups = [ "acme" ];

  security.acme = {
    acceptTerms = true;
    defaults.email = "Richie@tmmworkshop.com";

    certs."gitea.tmmworkshop.com" = {
      webroot = "/var/lib/acme/.challenges";
      group = "acme";
      reloadServices = [ "haproxy.service" ];
    };

    certs."audiobookshelf.tmmworkshop.com" = {
      webroot = "/var/lib/acme/.challenges";
      group = "acme";
      reloadServices = [ "haproxy.service" ];
    };

    certs."cache.tmmworkshop.com" = {
      webroot = "/var/lib/acme/.challenges";
      group = "acme";
      reloadServices = [ "haproxy.service" ];
    };

    certs."jellyfin.tmmworkshop.com" = {
      webroot = "/var/lib/acme/.challenges";
      group = "acme";
      reloadServices = [ "haproxy.service" ];
    };

    certs."share.tmmworkshop.com" = {
      webroot = "/var/lib/acme/.challenges";
      group = "acme";
      reloadServices = [ "haproxy.service" ];
    };
  };

  # Minimal nginx to serve ACME HTTP-01 challenge files for HAProxy
  services.nginx = {
    enable = true;
    virtualHosts."acme-challenge" = {
      listen = [
        {
          addr = "127.0.0.1";
          port = 8402;
        }
      ];
      locations."/.well-known/acme-challenge/" = {
        root = "/var/lib/acme/.challenges";
      };
    };
  };

  # Ensure the challenge directory exists with correct permissions
  systemd.tmpfiles.rules = [
    "d /var/lib/acme/.challenges 0750 acme acme - -"
    "d /var/lib/acme/.challenges/.well-known 0750 acme acme - -"
    "d /var/lib/acme/.challenges/.well-known/acme-challenge 0750 acme acme - -"
  ];

  users.users.nginx.extraGroups = [ "acme" ];
}
