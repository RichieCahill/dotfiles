{
  imports = [
    ../../users/richie
    ../../common/global
    ../../common/optional/systemd-boot.nix
    ../../common/optional/zerotier.nix
    ./hardware.nix
  ];

  networking = {
    hostName = "router";
    hostId = "c58bbb8b";
    firewall.enable = true;
    networkmanager.enable = true;
  };

  security.rtkit.enable = true;

  services = {

    openssh.ports = [ 972 ];

    snapshot_manager.enable = true;

    zfs = {
      trim.enable = true;
      autoScrub.enable = true;
    };
  };

  system.stateVersion = "24.05";
}
