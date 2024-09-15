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

  zramSwap.enable = true;

  security.auditd.enable = lib.mkDefault true;

  programs = {
    zsh.enable = true;
    fish.enable = true;
  };

  users.mutableUsers = lib.mkDefault true;

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    extraSpecialArgs = {inherit inputs outputs;};
  };

  nixpkgs.config.allowUnfree = true;

  hardware.enableRedistributableFirmware = true;
}
