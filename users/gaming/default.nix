{
  pkgs,
  config,
  ...
}: 
{
  users = {
    users.gaming = {
      isNormalUser = true;
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
