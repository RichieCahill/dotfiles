let
  vars = import ../vars.nix;
in
{
  networking.firewall = {
    allowedTCPPorts = [
      6882
      8081
      8118
    ];
    allowedUDPPorts = [ 6882 ];
  };
  virtualisation.oci-containers.containers.qbitvpn = {
    image = "binhex/arch-qbittorrentvpn:5.0.3-1-01";
    devices = [ "/dev/net/tun:/dev/net/tun" ];
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
    environmentFiles = [ "${vars.storage_secrets}/docker/qbitvpn" ];
    autoStart = true;
  };
}
