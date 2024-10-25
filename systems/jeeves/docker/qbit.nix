let
  vars = import ../vars.nix;
in
{
  networking.firewall = {
    allowedTCPPorts = [ 6881 8082 29432 ]; 
    allowedUDPPorts = [ 6881 ];
  };
  virtualisation.oci-containers.containers.qbit = {
    image = "ghcr.io/linuxserver/qbittorrent:latest";
    ports = [
      "6881:6881"
      "6881:6881/udp"
      "8082:8082"
      "29432:29432"
    ];
    volumes = [
      "${vars.media_docker_configs}/qbit:/config"
      "${vars.torrenting_qbit}:/data"
    ];
    environment = {
      PUID = "600";
      PGID = "100";
      TZ = "America/New_York";
      WEBUI_PORT = "8082";
    };
    autoStart = true;
  };
}
