let
  vars = import ../vars.nix;
in
{
  networking.firewall.allowedTCPPorts = [
    3000
  ];

  services.grafana = {
    enable = true;
    dataDir = "${vars.media_services}/grafana";
    settings = {
      server.http_addr = "0.0.0.0";
    };
  };
}
