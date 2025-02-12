{
  pkgs,
  config,
  ...
}:
let
  ifTheyExist = groups: builtins.filter (group: builtins.hasAttr group config.users.groups) groups;
in
{

  sops.secrets.brendan_password = {
    sopsFile = ../secrets.yaml;
    neededForUsers = true;
  };

  users = {
    users.brendan = {
      isNormalUser = true;

      hashedPasswordFile = "${config.sops.secrets.brendan_password.path}";

      shell = pkgs.zsh;
      group = "brendan";
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
      uid = 1001;
    };

    groups.brendan.gid = 1001;
  };

  home-manager.users.brendan = import ./systems/${config.networking.hostName}.nix;
}
