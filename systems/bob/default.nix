{ self, ... }:
{
  imports = [
    "${self}/users/richie"
    "${self}/users/gaming"
    "${self}/common/global"
    "${self}/common/optional/desktop.nix"
    "${self}/common/optional/docker.nix"
    "${self}/common/optional/scanner.nix"
    "${self}/common/optional/steam.nix"
    "${self}/common/optional/syncthing_base.nix"
    "${self}/common/optional/systemd-boot.nix"
    "${self}/common/optional/update.nix"
    "${self}/common/optional/yubikey.nix"
    "${self}/common/optional/zerotier.nix"
    "${self}/common/optional/nvidia.nix"
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
