{ inputs, self, ... }:
{
  imports = [
    "${self}/users/richie"
    "${self}/common/global"
    "${self}/common/optional/docker.nix"
    "${self}/common/optional/ssh_decrypt.nix"
    "${self}/common/optional/syncthing_base.nix"
    "${self}/common/optional/systemd-boot.nix"
    "${self}/common/optional/update.nix"
    "${self}/common/optional/zerotier.nix"
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
