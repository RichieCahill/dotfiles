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
    kernelPackages = lib.mkDefault (
      pkgs.linuxPackages_6_12.extend (
        self: super: {
          kernel = super.kernel.override {
            argsOverride = {
              version = "6.12.52";
              modDirVersion = "6.12.52";
              src = pkgs.fetchurl {
                url = "https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.12.52.tar.xz";
                sha256 = "sha256-tIUM9nCgMscPOLcTon1iBGxfdHyvAoxfULGPmGBqnrE=";
              };
            };
          };
        }
      )
    );
    zfs.package = lib.mkDefault pkgs.zfs_2_3;
  };

  hardware.enableRedistributableFirmware = true;

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    extraSpecialArgs = { inherit inputs outputs; };
    backupFileExtension = "backup";
  };

  nixpkgs = {
    overlays = builtins.attrValues outputs.overlays;
    config.allowUnfree = true;
  };

  services = {
    # firmware update
    fwupd.enable = true;

    snapshot_manager = {
      enable = lib.mkDefault true;
      PYTHONPATH = "${inputs.self}/";
    };

    zfs = {
      trim.enable = lib.mkDefault true;
      autoScrub.enable = lib.mkDefault true;
    };
  };

  powerManagement.powertop.enable = lib.mkDefault true;

  programs.zsh.enable = true;

  security = {
    auditd.enable = lib.mkDefault true;
    sudo-rs = {
      enable = true;
      execWheelOnly = true;
    };
    sudo.enable = false;
  };

  users.mutableUsers = lib.mkDefault false;

  zramSwap = {
    enable = lib.mkDefault true;
    priority = 1000;
  };
}
