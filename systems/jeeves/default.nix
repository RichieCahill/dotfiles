let
  vars = import ./vars.nix;
in
{
  imports = [
    ../../users/richie
    ../../common/global
    ../../common/optional/ssh_decrypt.nix
    ../../common/optional/syncthing_base.nix
    ../../common/optional/zerotier.nix
    ./arch_mirror.nix
    ./docker
    ./hardware.nix
    ./home_assistant.nix
    ./networking.nix
    ./programs.nix
    ./services.nix
    ./syncthing.nix
  ];

  boot.zfs.extraPools = [
    "media"
    "storage"
    "torrenting"
  ];

  services = {
    openssh.ports = [ 629 ];

    nix-serve = {
      enable = true;
      secretKeyFile = "${vars.storage_secrets}/services/nix-cache/cache-priv-key.pem";
    };

    plex = {
      enable = true;
      dataDir = vars.media_plex;
      openFirewall = true;
    };

    smartd.enable = true;

    snapshot_manager = {
      enable = true;
      path = ./snapshot_config.toml;
    };

    sysstat.enable = true;

    zfs = {
      trim.enable = true;
      autoScrub.enable = true;
    };
  };

  system.stateVersion = "24.05";
}
