let
  vars = import ../vars.nix;
in
{
  virtualisation.oci-containers.containers = {
    qbit = {
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
    qbitvpn = {
      image = "binhex/arch-qbittorrentvpn:latest";
      extraOptions = [ "--cap-add=NET_ADMIN" ];
      ports = [
        "6882:6881"
        "6882:6881/udp"
        "8081:8081"
        "8118:8118"
      ];
      volumes = [
        "${vars.media_docker_configs}/qbitvpn:/config"
        "${vars.torrenting_qbitvpn}:/data"
        "/etc/localtime:/etc/localtime:ro"
      ];
      environment = {
        WEBUI_PORT = "8081";
        PUID = "600";
        PGID = "100";
        VPN_ENABLED = "yes";
        VPN_CLIENT = "openvpn";
        STRICT_PORT_FORWARD = "yes";
        ENABLE_PRIVOXY = "yes";
        LAN_NETWORK = "192.168.90.0/24";
        NAME_SERVERS = "1.1.1.1,1.0.0.1";
        UMASK = "000";
        DEBUG = "false";
        DELUGE_DAEMON_LOG_LEVEL = "debug";
        DELUGE_WEB_LOG_LEVEL = "debug";
      };
      environmentFiles = ["${vars.storage_secrets}/docker/qbitvpn"];
      autoStart = true;
    };
    prowlarr = {
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
    sonarr = {
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
  };
}
