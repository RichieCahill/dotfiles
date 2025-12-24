{
  config,
  lib,
  outputs,
  ...
}:

with lib;

let
  vars = import ../vars.nix;
  cfg = config.services.nix_builder;
in
{
  options.services.nix_builder = {
    bridgeName = mkOption {
      type = types.str;
      default = "br-nix-builder";
      description = "Bridge name for the builder containers.";
    };

    containers = mkOption {
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
  };

  config = {
    containers = mapAttrs (
      name: containerCfg:
      mkIf containerCfg.enable {
        autoStart = true;
        privateNetwork = true;
        hostBridge = cfg.bridgeName;
        ephemeral = true;
        bindMounts = {
          storage = {
            hostPath = "/zfs/media/github-runners/${name}";
            mountPoint = "/zfs/media/github-runners/${name}";
            isReadOnly = false;
          };
          host-nix = {
            mountPoint = "/host-nix/var/nix/daemon-socket";
            hostPath = "/nix/var/nix/daemon-socket";
            isReadOnly = false;
          };
          secrets = {
            hostPath = "${vars.secrets}/services/github-runners/${name}";
            mountPoint = "${vars.secrets}/services/github-runners/${name}";
            isReadOnly = true;
          };
        };
        config =
          {
            config,
            pkgs,
            lib,
            ...
          }:
          {
            networking = {
              useDHCP = lib.mkDefault true;
              interfaces.eth0.useDHCP = true;
            };
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
              sandbox = true;
              allowed-users = [ "github-runners" ];
              trusted-users = [
                "root"
                "github-runners"
              ];
            };
            nixpkgs = {
              overlays = builtins.attrValues outputs.overlays;
              config.allowUnfree = true;
            };
            services.github-runners.${name} = {
              enable = true;
              replace = true;
              workDir = "/zfs/media/github-runners/${name}";
              url = "https://github.com/RichieCahill/dotfiles";
              extraLabels = [ "nixos" ];
              tokenFile = "${vars.secrets}/services/github-runners/${name}";
              user = "github-runners";
              group = "github-runners";
              extraPackages = with pkgs; [
                nixfmt-rfc-style
                nixos-rebuild
                treefmt
                my_python
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
    ) cfg.containers;
  };
}
