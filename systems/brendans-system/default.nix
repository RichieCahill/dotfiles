{
  imports = [
    ../../users/brendan
    ../../common/global
    ../../common/optional/desktop.nix
    ../../common/optional/docker.nix
    ../../common/optional/steam.nix
    ../../common/optional/systemd-boot.nix
    ../../common/optional/update.nix
    ../../common/optional/zerotier.nix
    ./hardware.nix
    ./nvidia.nix
    ./programs.nix
  ];

  networking = {
    hostName = "brendans-system";
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
