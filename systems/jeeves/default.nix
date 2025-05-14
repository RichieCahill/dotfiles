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
    ./networking.nix
    ./nvidia.nix
    ./programs.nix
    ./runners
    ./services
    ./services_accounts.nix
    ./syncthing.nix
  ];

  services = {
    openssh.ports = [ 629 ];

    smartd.enable = true;

    snapshot_manager.path = ./snapshot_config.toml;
  };

  system.stateVersion = "24.05";
}
