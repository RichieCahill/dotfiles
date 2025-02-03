let
  vars = import ../vars.nix;
in
{
  virtualisation.oci-containers.containers = {
    uptime_kuma = {
      ports = [ "3001:3001" ];
      image = "louislam/uptime-kuma:1.23.16-debian";
      volumes = [
        "${vars.media_docker_configs}/uptime_kuma:/app/data"
        "/var/run/docker.sock:/var/run/docker.sock"
      ];
      extraOptions = [ "--network=web" ];
      autoStart = true;
    };
  };
}
