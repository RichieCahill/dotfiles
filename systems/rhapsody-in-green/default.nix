{ inputs, ... }:
{
  imports = [
    "${inputs.self}/users/richie"
    "${inputs.self}/common/global"
    "${inputs.self}/common/optional/desktop.nix"
    "${inputs.self}/common/optional/docker.nix"
    "${inputs.self}/common/optional/steam.nix"
    "${inputs.self}/common/optional/syncthing_base.nix"
    "${inputs.self}/common/optional/systemd-boot.nix"
    "${inputs.self}/common/optional/yubikey.nix"
    "${inputs.self}/common/optional/zerotier.nix"
    ./hardware.nix
    ./llms.nix
    ./open_webui.nix
    ./qmk.nix
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
