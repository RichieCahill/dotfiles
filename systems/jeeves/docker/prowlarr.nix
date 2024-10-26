let
  vars = import ../vars.nix;
in
{
  networking.firewall.allowedTCPPorts = [ 9696 ];
  virtualisation.oci-containers.containers.prowlarr = {
    image = "ghcr.io/linuxserver/prowlarr:latest";
    ports = [ "9696:9696" ];
    environment = {
      PUID = "600";
      PGID = "100";
      TZ = "America/New_York";
    };
    volumes = [ "${vars.media_docker_configs}/prowlarr:/config" ];
    autoStart = true;
  };
}
