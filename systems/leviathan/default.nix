{ inputs, ... }:
{
  imports = [
    "${inputs.self}/users/elise"
    "${inputs.self}/users/richie"
    "${inputs.self}/common/global"
    "${inputs.self}/common/optional/desktop.nix"
    "${inputs.self}/common/optional/steam.nix"
    "${inputs.self}/common/optional/systemd-boot.nix"
    "${inputs.self}/common/optional/update.nix"
    "${inputs.self}/common/optional/zerotier.nix"
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
