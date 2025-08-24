{
  pkgs,
  config,
  ...
}:
let
  ifTheyExist = groups: builtins.filter (group: builtins.hasAttr group config.users.groups) groups;
in
{

  sops.secrets.elise_password = {
    sopsFile = ../secrets.yaml;
    neededForUsers = true;
  };

  users = {
    users.elise = {
      isNormalUser = true;

      hashedPasswordFile = "${config.sops.secrets.elise_password.path}";

      shell = pkgs.zsh;
      group = "elise";
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
      uid = 1010;
    };

    groups.elise.gid = 1010;
  };

  home-manager.users.elise = import ./systems/${config.networking.hostName}.nix;
}
