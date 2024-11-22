{  lib, pkgs, ... }:
{
  systemd = {
    services."autopull@dotfiles" = {
      requires = [ "multi-user.target" ];
      after = [ "multi-user.target" ];
      description = "Pull the latest data for dotfiles";
      serviceConfig = {
        Type = "oneshot";
        User = "root";
        WorkingDirectory = /root/dotfiles;
        ExecStart = "${pkgs.git}/bin/git pull --all --prune";
      };
    };
    timers."autopull@dotfiles" = {
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnBootSec = "1h";
        OnUnitActiveSec = "1h";
        Unit = "autopull@dotfiles.service";
      };
    };
  };

  system.autoUpgrade = {
    enable = lib.mkDefault true;
    flags = [ "--accept-flake-config" ];
    randomizedDelaySec = "1h";
    persistent = true;
    flake = "github:RAD-Development/nix-dotfiles";
  };
}
