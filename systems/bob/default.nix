{ inputs, ... }:
{
  imports = [
    "${inputs.self}/users/richie"
    "${inputs.self}/users/gaming"
    "${inputs.self}/common/global"
    "${inputs.self}/common/optional/desktop.nix"
    "${inputs.self}/common/optional/docker.nix"
    "${inputs.self}/common/optional/scanner.nix"
    "${inputs.self}/common/optional/steam.nix"
    "${inputs.self}/common/optional/syncthing_base.nix"
    "${inputs.self}/common/optional/systemd-boot.nix"
    "${inputs.self}/common/optional/update.nix"
    "${inputs.self}/common/optional/yubikey.nix"
    "${inputs.self}/common/optional/zerotier.nix"
    "${inputs.self}/common/optional/nvidia.nix"
    ./hardware.nix
    ./syncthing.nix
    ./llms.nix
  ];

  networking = {
    hostName = "bob";
    hostId = "7c678a41";
    firewall.enable = true;
    networkmanager.enable = true;
  };

  services = {
    displayManager = {
      enable = true;
      autoLogin = {
        user = "gaming";
        enable = true;
      };
      defaultSession = "plasma";
    };

    openssh.ports = [ 262 ];

    snapshot_manager.path = ./snapshot_config.toml;
  };

  system.stateVersion = "24.05";
}
