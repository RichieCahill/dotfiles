let
  vars = import ../vars.nix;
in
{
  config,
  ...
}:
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

  sops.secrets.gcw_password = {
    sopsFile = ../../../users/secrets.yaml;
    neededForUsers = true;
  };

  users = {
    users.gcw = {
      isSystemUser = true;
      hashedPasswordFile = "${config.sops.secrets.gcw_password.path}";
      group = "gcw";
    };
    groups.gcw = { };
  };
}
