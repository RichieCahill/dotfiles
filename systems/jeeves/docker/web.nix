let
  vars = import ../vars.nix;
in
{
  virtualisation.oci-containers.containers = {
    audiobookshelf = {
      image = "ghcr.io/advplyr/audiobookshelf:latest";
      ports = [ "13378:80" ];
      volumes = [
        "${vars.media_docker_configs}/audiobookshelf:/config"
        "${vars.media_docker_configs}/audiobookshelf:/metadata"
        "${vars.storage_library}/audiobooks:/audiobooks"
        "${vars.storage_library}/books:/books"
      ];
      environment = {
        TZ = "America/New_York";
      };
      extraOptions = [ "--network=web" ];
      autoStart = true;
    };
    grafana = {
      image = "grafana/grafana-enterprise:latest";
      volumes = [ "${vars.media_docker_configs}/grafana:/var/lib/grafana" ];
      user = "600:600";
      extraOptions = [ "--network=web" ];
      autoStart = true;
    };
    haproxy = {
      image = "haproxy:latest";
      user = "600:600";
      environment = {
        TZ = "Etc/EST";
      };
      volumes = [
        "${vars.storage_secrets}/docker/cloudflare.pem:/etc/ssl/certs/cloudflare.pem"
        "${./haproxy.cfg}:/usr/local/etc/haproxy/haproxy.cfg"
      ];
      dependsOn = [
        "arch_mirror"
        "audiobookshelf"
        "filebrowser"
        "grafana"
        "uptime_kuma"
      ];
      extraOptions = [ "--network=web" ];
      autoStart = true;
    };
    cloud_flare_tunnel = {
      image = "cloudflare/cloudflared:latest";
      user = "600:600";
      cmd = [
        "tunnel"
        "run"
      ];
      environmentFiles = ["${vars.storage_secrets}/docker/cloud_flare_tunnel"];
      dependsOn = [ "haproxy" ];
      extraOptions = [ "--network=web" ];
      autoStart = true;
    };
  };
}
