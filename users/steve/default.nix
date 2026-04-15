{
  pkgs,
  config,
  ...
}:
let
  ifTheyExist = groups: builtins.filter (group: builtins.hasAttr group config.users.groups) groups;
in
{

  users = {
    users.steve = {
      isNormalUser = true;

      shell = pkgs.zsh;
      group = "steve";
      openssh.authorizedKeys.keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJH03VzDbUhzfhvwD+OsYh6GobODYaI9jdNdzWQoqFsp matth@Jove" # cspell:disable-line
      ];
      extraGroups = [
        "audio"
        "video"
        "wheel"
        "users"
      ]
      ++ ifTheyExist [
        "dialout"
        "docker"
        "hass"
        "libvirtd"
        "networkmanager"
        "plugdev"
        "scanner"
        "transmission"
        "uaccess"
        "wireshark"
      ];
      uid = 1005;
    };

    groups.steve.gid = 1005;
  };
  home-manager.users.steve = import ./systems/${config.networking.hostName}.nix;
}
