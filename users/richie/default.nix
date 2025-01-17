{
  pkgs,
  config,
  ...
}: let
  ifTheyExist = groups: builtins.filter (group: builtins.hasAttr group config.users.groups) groups;
in {

  sops.secrets.richie_password = {
    sopsFile = ../secrets.yaml;
    neededForUsers = true;
  };

  users = {
    users.richie = {
      isNormalUser = true;

      hashedPasswordFile = "${config.sops.secrets.richie_password.path}";

      shell = pkgs.zsh;
      group = "richie";
      openssh.authorizedKeys.keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJYZFsc9CSH03ZUP7y81AHwSyjLwFmcshVFCyxDcYhBT rhapsody-in-green" # cspell:disable-line
      ];
      extraGroups =
      [
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
        "uaccess"
        "wireshark"
      ];
      uid = 1000;
    };

    groups.richie.gid = 1000;
  };

  home-manager.users.richie = import ./systems/${config.networking.hostName}.nix; 
}
