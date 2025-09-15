let
  vars = import ./vars.nix;
in
{
  imports = [
    ../../users/richie
    ../../users/math
    ../../common/global
    ../../common/optional/docker.nix
    ../../common/optional/ssh_decrypt.nix
    ../../common/optional/syncthing_base.nix
    ../../common/optional/update.nix
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

  services = {
    openssh.ports = [ 629 ];

    smartd.enable = true;

    snapshot_manager = {
      path = ./snapshot_config.toml;
      EnvironmentFile = "${vars.secrets}/services/snapshot_manager";
    };

    zerotierone.joinNetworks = [ "a09acf02330d37b9" ];
  };

  system.stateVersion = "24.05";
}
