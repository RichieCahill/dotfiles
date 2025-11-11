{ inputs, ... }:
let
  vars = import ./vars.nix;
in
{
  imports = [
    "${inputs.self}/users/richie"
    "${inputs.self}/users/math"
    "${inputs.self}/users/dov"
    "${inputs.self}/common/global"
    "${inputs.self}/common/optional/docker.nix"
    "${inputs.self}/common/optional/ssh_decrypt.nix"
    "${inputs.self}/common/optional/syncthing_base.nix"
    "${inputs.self}/common/optional/update.nix"
    "${inputs.self}/common/optional/zerotier.nix"
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
