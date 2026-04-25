let
  domains = [
    "audiobookshelf"
    "cache"
    "gitea"
    "jellyfin"
    "share"
    "verilux"
  ];
  extraDomains = [ "www.norn-sight.com" ];

  makeCert = name: {
    name = "${name}.tmmworkshop.com";
    value = {
      webroot = "/var/lib/acme/.challenges";
      group = "acme";
      reloadServices = [ "haproxy.service" ];
    };
  };

  makeExtraCert = name: {
    inherit name;
    value = {
      webroot = "/var/lib/acme/.challenges";
      group = "acme";
      reloadServices = [ "haproxy.service" ];
    };
  };

  acmeServices =
    map (domain: "acme-${domain}.tmmworkshop.com.service") domains
    ++ map (domain: "acme-${domain}.service") extraDomains;
in
{
  users.users.haproxy.extraGroups = [ "acme" ];

  security.acme = {
    acceptTerms = true;
    defaults.email = "Richie@tmmworkshop.com";
    certs = builtins.listToAttrs ((map makeCert domains) ++ (map makeExtraCert extraDomains));
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

  # HAProxy needs certs to exist before it can bind :443.
  # NixOS's acme module generates self-signed placeholders on first boot
  # via acme-<domain>.service — just make HAProxy wait for them.
  systemd.services.haproxy = {
    after = acmeServices;
    wants = acmeServices;
  };
}
