let
  vars = import ../vars.nix;
in
{
  networking.firewall.allowedTCPPorts = [ 9696 8989 ];
  virtualisation.oci-containers.containers.sonarr = {
    image = "ghcr.io/linuxserver/sonarr:latest";
    ports = [ "8989:8989" ];
    environment = {
      PUID = "600";
      PGID = "100";
      TZ = "America/New_York";
    };
    volumes = [
      "${vars.media_docker_configs}/sonarr:/config"
      "${vars.storage_plex}/tv:/tv"
      "${vars.torrenting_qbitvpn}:/data"
    ];
    autoStart = true;
  };
}
