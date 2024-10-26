let
  vars = import ../vars.nix;
in
{
  virtualisation.oci-containers.containers.grafana = {
    image = "grafana/grafana-enterprise:latest";
    volumes = [ "${vars.media_docker_configs}/grafana:/var/lib/grafana" ];
    user = "600:600";
    extraOptions = [ "--network=web" ];
    autoStart = true;
  };
}
