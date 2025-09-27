{ inputs, ... }:
{
  imports = [
    ../../users/richie
    ../../common/global
    ../../common/optional/docker.nix
    ../../common/optional/ssh_decrypt.nix
    ../../common/optional/syncthing_base.nix
    ../../common/optional/systemd-boot.nix
    ../../common/optional/update.nix
    ../../common/optional/zerotier.nix
    ./docker
    ./hardware.nix
    ./programs.nix
    ./services
    ./syncthing.nix
    inputs.nixos-hardware.nixosModules.framework-11th-gen-intel
  ];

  networking = {
    hostName = "brain";
    hostId = "93a06c6e";
    firewall.enable = true;
    networkmanager.enable = true;
  };

  services = {
    openssh.ports = [ 129 ];

    smartd.enable = true;
  };

  system.stateVersion = "25.05";
}
