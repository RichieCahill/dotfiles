{
  pkgs,
  config,
  ...
}: let
  ifTheyExist = groups: builtins.filter (group: builtins.hasAttr group config.users.groups) groups;
in {
  users.users.richie = {
    isNormalUser = true;
    shell = pkgs.zsh;
    group = "richie";
    openssh.authorizedKeys.keys = [
      "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIPtuYhiJHRTYhNaDmTcJOqJASk7D8mIn6u3F1IN5AFJ bob" # cspell:disable-line
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

  users.groups.richie = {
    gid = 1000;
  };

  home-manager.users.richie = import ./systems/${config.networking.hostName}.nix; 
}
