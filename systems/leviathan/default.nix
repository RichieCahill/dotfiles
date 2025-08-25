{ inputs, ... }:
{
  imports = [
    ../../users/elise
    ../../users/richie
    ../../common/global
    ../../common/optional/desktop.nix
    ../../common/optional/steam.nix
    ../../common/optional/systemd-boot.nix
    ../../common/optional/update.nix
    ./hardware.nix
    inputs.nixos-hardware.nixosModules.framework-13-7040-amd
  ];

  networking = {
    hostName = "leviathan";
    hostId = "cb9b64d8";
    firewall.enable = true;
    networkmanager.enable = true;
  };

  services = {
    openssh.ports = [ 332 ];
  };

  system.stateVersion = "25.05";
}
