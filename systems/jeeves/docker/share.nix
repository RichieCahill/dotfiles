let
  vars = import ../vars.nix;
in
{
  virtualisation.oci-containers.containers.share = {
    image = "ubuntu/apache2:2.4-22.04_beta";
    ports = [ "8091:80" ];
    volumes = [
      "${../../../common/docker_templates}/file_server/sites/:/etc/apache2/sites-enabled/"
      "${vars.share}:/data"
    ];
    extraOptions = [ "--network=web" ];
    autoStart = true;
  };
}
