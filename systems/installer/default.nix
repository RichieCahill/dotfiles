{
  inputs,
  lib,
  pkgs,
  modulesPath,
  ...
}:
{
  imports = [ (modulesPath + "/installer/cd-dvd/installation-cd-minimal.nix") ];

  environment.systemPackages = [
    inputs.system_tools.packages.x86_64-linux.default
  ];

  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";

  systemd.services.sshd.wantedBy = pkgs.lib.mkForce [ "multi-user.target" ];

  users.users.root.openssh.authorizedKeys.keys = [
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJYZFsc9CSH03ZUP7y81AHwSyjLwFmcshVFCyxDcYhBT rhapsody-in-green" # cspell:disable-line
  ];
}
