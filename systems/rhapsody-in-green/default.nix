{ inputs, self, ... }:
{
  imports = [
    "${self}/users/richie"
    "${self}/common/global"
    "${self}/common/optional/desktop.nix"
    "${self}/common/optional/docker.nix"
    "${self}/common/optional/steam.nix"
    "${self}/common/optional/syncthing_base.nix"
    "${self}/common/optional/systemd-boot.nix"
    "${self}/common/optional/yubikey.nix"
    "${self}/common/optional/zerotier.nix"
    ./hardware.nix
    ./llms.nix
    ./syncthing.nix
    inputs.nixos-hardware.nixosModules.framework-13-7040-amd
  ];

  networking = {
    hostName = "rhapsody-in-green";
    hostId = "6404140d";
    firewall = {
      enable = true;
      allowedTCPPorts = [ ];
    };
    networkmanager.enable = true;
  };

  services = {
    openssh.ports = [ 922 ];
  };

  system.stateVersion = "24.05";
}
