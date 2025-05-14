{
  config,
  ...
}:
{

  sops.secrets.unifi_password = {
    sopsFile = ../../users/secrets.yaml;
    neededForUsers = true;
  };

  users = {

    users.unifi = {
      isSystemUser = true;
      group = "unifi";
      extraGroups = [ "samba" ];
      hashedPasswordFile = "${config.sops.secrets.unifi_password.path}";
    };
    groups.unifi = { };
  };
}
