let
  vars = import ../vars.nix;
in
{
  virtualisation.oci-containers.containers = {
    cloud_flare_tunnel = {
      image = "cloudflare/cloudflared:2025.1.1";
      user = "600:600";
      cmd = [
        "tunnel"
        "run"
      ];
      environmentFiles = ["${vars.storage_secrets}/docker/cloud_flare_tunnel"];
      extraOptions = [ "--network=web" ];
      autoStart = true;
    };
  };
}
