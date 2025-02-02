let
  vars = import ../vars.nix;
in
{
  virtualisation.oci-containers.containers = {
    haproxy = {
      image = "haproxy:3.1";
      user = "600:600";
      environment = {
        TZ = "Etc/EST";
      };
      volumes = [
        "${vars.storage_secrets}/docker/cloudflare.pem:/etc/ssl/certs/cloudflare.pem"
        "${./haproxy.cfg}:/usr/local/etc/haproxy/haproxy.cfg"
      ];
      dependsOn = [
        "uptime_kuma"
      ];
      extraOptions = [ "--network=web" ];
      autoStart = true;
    };
    cloud_flare_tunnel = {
      image = "cloudflare/cloudflared:2025.1.1";
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
