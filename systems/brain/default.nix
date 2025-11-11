{ inputs, ... }:
{
  imports = [
    "${inputs.self}/users/richie"
    "${inputs.self}/common/global"
    "${inputs.self}/common/optional/docker.nix"
    "${inputs.self}/common/optional/ssh_decrypt.nix"
    "${inputs.self}/common/optional/syncthing_base.nix"
    "${inputs.self}/common/optional/systemd-boot.nix"
    "${inputs.self}/common/optional/update.nix"
    "${inputs.self}/common/optional/zerotier.nix"
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

  hardware.bluetooth = {
    enable = true;
    powerOnBoot = true;
  };

  services = {
    openssh.ports = [ 129 ];

    smartd.enable = true;
  };

  system.stateVersion = "25.05";
}
