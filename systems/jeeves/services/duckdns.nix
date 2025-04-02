let
  vars = import ../vars.nix;
in
{
  services.duckdns = {
    enable = true;
    tokenFile = "${vars.secrets}/services/duckdns/token";
    domainsFile = "${vars.secrets}/services/duckdns/domains";
  };
}
