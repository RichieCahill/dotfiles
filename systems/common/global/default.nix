{
  config,
  lib,
  inputs,
  outputs,
  ...
}:
{
  imports = [
    inputs.home-manager.nixosModules.home-manager
    ./docker.nix
    ./fail2ban.nix
    ./libs.nix
    ./locale.nix
    ./nh.nix
    ./nix.nix
    ./programs.nix
    ./ssh.nix
  ];

  boot = {
    kernelPackages = config.boot.zfs.package.latestCompatibleLinuxPackages;
    tmp.useTmpfs = true;
  };

  hardware.enableRedistributableFirmware = true;

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    extraSpecialArgs = {inherit inputs outputs;};
  };

  nixpkgs.config.allowUnfree = true;

  programs = {
    zsh.enable = true;
    fish.enable = true;
  };

  security.auditd.enable = lib.mkDefault true;

  users.mutableUsers = lib.mkDefault true;

  zramSwap = {
    enable = lib.mkDefault true;
    priority = 1000;
  };
}
