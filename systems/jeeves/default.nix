let
  vars = import ./vars.nix;
in
{
  imports = [
    ../../users/richie
    ../../common/global
    ../../common/optional/docker.nix
    ../../common/optional/ssh_decrypt.nix
    ../../common/optional/syncthing_base.nix
    ../../common/optional/zerotier.nix
    ./docker
    ./hardware.nix
    ./home_assistant.nix
    ./jellyfin.nix
    ./networking.nix
    ./programs.nix
    ./runner.nix
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


    smartd.enable = true;

    snapshot_manager.path = ./snapshot_config.toml;
  };

  system.stateVersion = "24.05";
}
