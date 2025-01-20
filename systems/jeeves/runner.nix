{ pkgs, ... }:
let
  vars = import ./vars.nix;
in
{
  users = {
    users.github-runners = {
      isSystemUser = true;
      group = "github-runners";
      uid = 601;
    };
    groups.github-runners.gid = 601;
  };
  
  services.github-runners.nix_builder = {
    enable = true;
    replace = true;
    workDir = "/zfs/media/github-runners/nix_builder/";
    url = "https://github.com/RichieCahill/dotfiles";
    extraLabels = [ "nixos" ];
    tokenFile = "${vars.storage_secrets}/services/github_runners/nix_builder";
    user = "github-runners";
    group = "github-runners";
    extraPackages = [ pkgs.nixos-rebuild ];
    # extraEnvironment
  };

  containers.nix-builder-1 = {
    autoStart = true;
    bindMounts = {
      "/test" = {
        mountPoint = "/zfs/media/github-runners/nix_builder_1";
        isReadOnly = false;
      };
      "/secrets".mountPoint = "${vars.storage_secrets}/services/github_runners/nix_builder_1";
    };
    config = { config, pkgs, lib, ... }: {
      users = {
        users.github-runners = {
          isSystemUser = true;
          group = "github-runners";
          uid = 601;
        };
        groups.github-runners.gid = 601;
      };
      services.github-runners.nix_builder_1 = {
        enable = true;
        replace = true;
        workDir = "/zfs/media/github-runners/nix_builder_1";
        url = "https://github.com/RichieCahill/dotfiles";
        extraLabels = [ "nixos" ];
        tokenFile = "${vars.storage_secrets}/services/github_runners/nix_builder_1";
        user = "github-runners";
        group = "github-runners";
        extraPackages = [ pkgs.nixos-rebuild ];
      };
      system.stateVersion = "24.11";
    };
  };
}
