{
  imports = [
    ../../users/richie
    ../../users/gaming
    ../../common/global
    ../../common/optional/desktop.nix
    ../../common/optional/docker.nix
    ../../common/optional/scanner.nix
    ../../common/optional/steam.nix
    ../../common/optional/syncthing_base.nix
    ../../common/optional/systemd-boot.nix
    ../../common/optional/update.nix
    ../../common/optional/yubikey.nix
    ../../common/optional/zerotier.nix
    ../../common/optional/nvidia.nix
    ./hardware.nix
    ./syncthing.nix
    ./games.nix
    ./llms.nix
  ];

  networking = {
    hostName = "bob";
    hostId = "7c678a41";
    firewall.enable = true;
    networkmanager.enable = true;
  };

  services = {
    displayManager = {
      enable = true;
      autoLogin = {
        user = "gaming";
        enable = true;
      };
      defaultSession = "plasma";
    };

    openssh.ports = [ 262 ];
  };

  system.stateVersion = "24.05";
}
