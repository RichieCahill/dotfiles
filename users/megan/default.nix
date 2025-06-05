{
  pkgs,
  config,
  ...
}:
{
  sops.secrets.megan_password = {
    sopsFile = ../secrets.yaml;
    neededForUsers = true;
  };

  users = {
    users.megan = {
      isNormalUser = true;
      hashedPasswordFile = "${config.sops.secrets.megan_password.path}";

      shell = pkgs.zsh;
      group = "megan";
      extraGroups = [
        "audio"
        "video"
        "users"
      ];
      uid = 1101;
    };

    groups.megan.gid = 1101;
  };
  home-manager.users.megan = import ./systems/${config.networking.hostName}.nix;
}
