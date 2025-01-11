{
  inputs,
  lib,
  outputs,
  pkgs,
  ...
}:
{
  imports = [
    inputs.home-manager.nixosModules.home-manager
    inputs.sops-nix.nixosModules.sops
    ./fail2ban.nix
    ./fonts.nix
    ./libs.nix
    ./locale.nix
    ./nh.nix
    ./nix.nix
    ./programs.nix
    ./ssh.nix
    ./snapshot_manager.nix
  ];

  boot = {
    tmp.useTmpfs = true;
    kernelPackages = lib.mkDefault pkgs.linuxPackages_6_12;
    zfs.package = lib.mkDefault pkgs.zfs;
  };

  hardware.enableRedistributableFirmware = true;

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    extraSpecialArgs = {inherit inputs outputs;};
    backupFileExtension = "backup";
  };

  nixpkgs = {
    overlays = builtins.attrValues outputs.overlays;
    config = {
      allowUnfree = true;
    };
  };

  services.fwupd.enable = true;

  programs.zsh.enable = true;

  security.auditd.enable = lib.mkDefault true;

  users.mutableUsers = lib.mkDefault false;

  zramSwap = {
    enable = lib.mkDefault true;
    priority = 1000;
  };
}
