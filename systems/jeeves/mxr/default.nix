{
  containers.mxr = {
    autoStart = true;
    ephemeral = true;
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
        systemd.services.mxr = {
          description = "mxr";
          after = [ "network.target" ];
          wantedBy = [ "multi-user.target" ];
          serviceConfig = {
            Type = "simple";
            User = "mxr";
            Group = "mxr";
            ExecStart = "curl -s https://raw.githubusercontent.com/RichieCahill/mxr/refs/heads/main/tools/installer.py | ${pkgs.python313}/bin/python";
            Restart = "on-failure";
          };
        };
        system.stateVersion = "24.11";
      };
  };
}
