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
    ../../common/optional/yubikey.nix
    ../../common/optional/zerotier.nix
    ./hardware.nix
    ./nvidia.nix
    ./syncthing.nix
    ./games.nix
  ];

  networking = {
    hostName = "bob";
    hostId = "7c678a41";
    firewall.enable = true;
    networkmanager.enable = true;
  };

  hardware = {
    pulseaudio.enable = false;
    bluetooth = {
      enable = true;
      powerOnBoot = true;
    };
  };

  security.rtkit.enable = true;

  services = {
    displayManager = {
      enable = true;
      autoLogin = {
        user = "gaming";
        enable = true;
      };
      defaultSession = "steam";
      # defaultSession = "plasma";
    };

    openssh.ports = [ 262 ];

    snapshot_manager.enable = true;

    zfs = {
      trim.enable = true;
      autoScrub.enable = true;
    };
  };

  system.stateVersion = "24.05";
}
