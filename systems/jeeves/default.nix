{ self, ... }:
let
  vars = import ./vars.nix;
in
{
  imports = [
    "${self}/users/richie"
    "${self}/users/math"
    "${self}/users/dov"
    "${self}/common/global"
    "${self}/common/optional/docker.nix"
    "${self}/common/optional/ssh_decrypt.nix"
    "${self}/common/optional/syncthing_base.nix"
    "${self}/common/optional/update.nix"
    "${self}/common/optional/zerotier.nix"
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
