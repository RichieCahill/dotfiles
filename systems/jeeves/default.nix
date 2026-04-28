{ inputs, ... }:
let
  vars = import ./vars.nix;
in
{
  imports = [
    "${inputs.self}/users/dov"
    "${inputs.self}/users/math"
    "${inputs.self}/users/richie"
    "${inputs.self}/users/steve"
    "${inputs.self}/common/global"
    "${inputs.self}/common/optional/docker.nix"
    "${inputs.self}/common/optional/monitoring-agent.nix"
    "${inputs.self}/common/optional/ssh_decrypt.nix"
    "${inputs.self}/common/optional/syncthing_base.nix"
    "${inputs.self}/common/optional/update.nix"
    "${inputs.self}/common/optional/zerotier.nix"
    ./monitoring
    ./docker
    ./services
    ./web_services
    ./hardware.nix
    ./networking.nix
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

  users.groups = {
    nornsight = { };
    nornsight-admin = { };
  };

  system.stateVersion = "24.05";
}
