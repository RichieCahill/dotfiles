{ config, lib, ... }:

with lib;

let
  vars = import ../vars.nix;
in
{
  options.services.nix_builder.containers = mkOption {
    type = types.attrsOf (
      types.submodule (
        { name, ... }:
        {
          options.enable = mkEnableOption "GitHub runner container";
        }
      )
    );
    default = { };
    description = "GitHub runner container configurations";
  };

  config.containers = mapAttrs (
    name: cfg:
    mkIf cfg.enable {
      autoStart = true;
      bindMounts = {
        "/storage" = {
          mountPoint = "/zfs/media/github-runners/${name}";
          isReadOnly = false;
        };
        "/secrets".mountPoint = "${vars.storage_secrets}/services/github-runners/${name}";
        "ssh-keys".mountPoint = "${vars.storage_secrets}/services/github-runners/id_ed25519_github-runners";
      };
      config =
        {
          config,
          pkgs,
          lib,
          ...
        }:
        {
          nix.settings = {
            trusted-substituters = [
              "https://cache.nixos.org"
              "https://cache.tmmworkshop.com"
              "https://nix-community.cachix.org"
            ];
            substituters = [
              "https://cache.nixos.org/?priority=2&want-mass-query=true"
              "https://cache.tmmworkshop.com/?priority=2&want-mass-query=true"
              "https://nix-community.cachix.org/?priority=10&want-mass-query=true"
            ];
            trusted-public-keys = [
              "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
              "cache.tmmworkshop.com:jHffkpgbmEdstQPoihJPYW9TQe6jnQbWR2LqkNGV3iA="
              "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
            ];
            experimental-features = [
              "flakes"
              "nix-command"
            ];
          };
          programs.ssh.extraConfig = ''
            Host jeeves
              Port 629
              User github-runners
              HostName 192.168.95.14
              IdentityFile ${vars.storage_secrets}/services/github-runners/id_ed25519_github-runners
              StrictHostKeyChecking no
              UserKnownHostsFile /dev/null
          '';
          services.github-runners.${name} = {
            enable = true;
            replace = true;
            workDir = "/zfs/media/github-runners/${name}";
            url = "https://github.com/RichieCahill/dotfiles";
            extraLabels = [ "nixos" ];
            tokenFile = "${vars.storage_secrets}/services/github-runners/${name}";
            user = "github-runners";
            group = "github-runners";
            extraPackages = with pkgs; [
              nixfmt-rfc-style
              nixos-rebuild
              openssh
              treefmt
            ];
          };
          users = {
            users.github-runners = {
              shell = pkgs.bash;
              isSystemUser = true;
              group = "github-runners";
              uid = 601;
            };
            groups.github-runners.gid = 601;
          };
          system.stateVersion = "24.11";
        };
    }
  ) config.services.nix_builder.containers;
}
