{ inputs, self, ... }:
{
  imports = [
    "${self}/users/elise"
    "${self}/users/richie"
    "${self}/common/global"
    "${self}/common/optional/desktop.nix"
    "${self}/common/optional/steam.nix"
    "${self}/common/optional/systemd-boot.nix"
    "${self}/common/optional/update.nix"
    "${self}/common/optional/zerotier.nix"
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
