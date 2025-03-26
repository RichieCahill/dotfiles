{
  imports = [
    ../../users/richie
    ../../common/global
    ../../common/optional/docker.nix
    ../../common/optional/ssh_decrypt.nix
    ../../common/optional/syncthing_base.nix
    ../../common/optional/zerotier.nix
    ./docker
    ./services
    ./hardware.nix
    ./networking.nix
    ./nvidia.nix
    ./programs.nix
    ./runners
    ./syncthing.nix
  ];

  boot.zfs.extraPools = [
    "media"
    "storage"
    "torrenting"
  ];

  powerManagement = { 
    cpuFreqGovernor = "ondemand";
    # scsiLinkPolicy = "min_power";
    # powertop.enable = true;
  };

  services = {
    openssh.ports = [ 629 ];

    smartd.enable = true;

    snapshot_manager.path = ./snapshot_config.toml;
  };

  system.stateVersion = "24.05";
}
