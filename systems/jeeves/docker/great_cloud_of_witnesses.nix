let
  vars = import ../vars.nix;
in
{
  virtualisation.oci-containers.containers.great_cloud_of_witnesses = {
    image = "ubuntu/apache2:2.4-22.04_beta";
    ports = [ "8092:80" ];
    volumes = [
      "${../../../common/docker_templates}/file_server/sites/:/etc/apache2/sites-enabled/"
      "${vars.services}/great_cloud_of_witnesses:/data"
      "/var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock"
    ];
    extraOptions = [ "--network=web" ];
    autoStart = true;
  };
}
