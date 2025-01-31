let
  vars = import ../vars.nix;
in
{
  services.duckdns = {
    enable = true;
    tokenFile = "${vars.storage_secrets}/services/duckdns/token";
    domainsFile = "${vars.storage_secrets}/services/duckdns/domains";
  };
}
