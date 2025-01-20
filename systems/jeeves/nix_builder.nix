{ config, lib, ... }:

with lib;

let
  vars = import ./vars.nix;
in
{
  options.services.nix_builder.containers = mkOption {
    type = types.attrsOf (types.submodule ({ name, ... }: {
      options.enable = mkEnableOption "GitHub runner container";
    }));
    default = {};
    description = "GitHub runner container configurations";
  };

  config.containers = mapAttrs (name: cfg:
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
      config = { config, pkgs, lib, ... }: {
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
            extraPackages = with pkgs; [ nixos-rebuild openssh unixtools.ping];
          };
          users = {
            users.github-runners = {
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
