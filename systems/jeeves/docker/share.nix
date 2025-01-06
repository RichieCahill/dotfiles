let
  vars = import ../vars.nix;
in
{
  virtualisation.oci-containers.containers.share = {
    image = "ubuntu/apache2:latest";
    volumes = [
      "${../../../common/docker_templates}/file_server/sites/:/etc/apache2/sites-enabled/"
      "${vars.media_share}:/data"
    ];
    extraOptions = [ "--network=web" ];
    autoStart = true;
  };
}
