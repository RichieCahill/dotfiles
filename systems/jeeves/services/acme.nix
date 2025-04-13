{ config, ... }:
let
  vars = import ../vars.nix;
in
{
  security.acme = {
    acceptTerms = true;
    defaults = {
      email = "themadmaker2@protonmail.com";
      dnsResolver = "1.1.1.1:53";
      extraLegoFlags = [
        "--dns-timeout=300"
      ];
    };
    certs."tmmworkshop.com" = {
      dnsProvider = "cloudflare";
      environmentFile = "${vars.secrets}/services/acme/cloudflare.txt";
      email = "themadmaker2@protonmail.com";
      group = config.services.haproxy.group;
    };
  };
}
