{
  imports = [
    ../../users/richie
    ../../common/global
    ../../common/optional/desktop.nix
    ../../common/optional/scanner.nix
    ../../common/optional/steam.nix
    ../../common/optional/syncthing_base.nix
    ../../common/optional/systemd-boot.nix
    ../../common/optional/zerotier.nix
    ../../common/optional/yubikey.nix
    ./hardware.nix
    ./nvidia.nix
    ./syncthing.nix
  ];

  networking = {
    hostName = "bob";
    networkmanager.enable = true;
    hostId = "7c678a41";
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

    displayManager.sddm.enable = true;

    openssh.ports = [ 262 ];

    printing.enable = true;

    pipewire = {
      enable = true;
      alsa.enable = true;
      alsa.support32Bit = true;
      pulse.enable = true;
    };

    snapshot_manager.enable = true;

    zfs = {
      trim.enable = true;
      autoScrub.enable = true;
    };
  };

  system.stateVersion = "24.05";
}
