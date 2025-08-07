{
  pkgs,
  config,
  ...
}:
let
  ifTheyExist = groups: builtins.filter (group: builtins.hasAttr group config.users.groups) groups;
in
{

  sops.secrets.math_password = {
    sopsFile = ../secrets.yaml;
    neededForUsers = true;
  };

  users = {
    users.math = {
      isNormalUser = true;

      hashedPasswordFile = "${config.sops.secrets.math_password.path}";

      shell = pkgs.zsh;
      group = "math";
      openssh.authorizedKeys.keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJYZFsc9CSH03ZUP7y81AHwSyjLwFmcshVFCyxDcYhBT rhapsody-in-green" # cspell:disable-line
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
      uid = 1003;
    };

    groups.math.gid = 1003;
  };

  home-manager.users.math = import ./systems/${config.networking.hostName}.nix;
}
