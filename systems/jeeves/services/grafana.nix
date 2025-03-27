let
  vars = import ../vars.nix;
in
{
  services.grafana = {
    enable = true;
    dataDir = "${vars.media_services}/grafana";
  };
}
