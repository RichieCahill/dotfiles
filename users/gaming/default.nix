{
  pkgs,
  config,
  ...
}: 
{
  sops.secrets.gaming_password = {
    sopsFile = ../secrets.yaml;
    neededForUsers = true;
  };

  users = {
    users.gaming = {
      isNormalUser = true;
      hashedPasswordFile = "${config.sops.secrets.gaming_password.path}";

      shell = pkgs.zsh;
      group = "gaming";
      extraGroups =
      [
        "audio"
        "video"
        "users"
      ];
      uid = 1100;
    };

    groups.gaming.gid = 1100;
  };
  home-manager.users.gaming = import ./systems/${config.networking.hostName}.nix; 
}
