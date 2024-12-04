{
  inputs,
  lib,
  ...
}: let
  flakeInputs = lib.filterAttrs (_: lib.isType "flake") inputs;
in {
  nix = {
    settings = {
      trusted-users = [
        "root"
        "@wheel"
      ];
      trusted-substituters = [
        "https://cache.nixos.org"
        "https://cache.tmmworkshop.com"
        "https://nix-community.cachix.org"
      ];
      substituters = [
        "https://cache.nixos.org/?priority=1&want-mass-query=true"
        "https://cache.tmmworkshop.com/?priority=1&want-mass-query=true"
        "https://nix-community.cachix.org/?priority=10&want-mass-query=true"
      ];
      trusted-public-keys = [
        "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
        "cache.tmmworkshop.com:jHffkpgbmEdstQPoihJPYW9TQe6jnQbWR2LqkNGV3iA="
        "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
      ];
      auto-optimise-store = lib.mkDefault true;
      experimental-features = [
        "nix-command"
        "flakes"
        "ca-derivations"
      ];
      warn-dirty = false;
      flake-registry = ""; # disable global flake registries
    };

    # Add each flake input as a registry and nix_path
    registry = lib.mapAttrs (_: flake: {inherit flake;}) flakeInputs;
    nixPath = lib.mapAttrsToList (n: _: "${n}=flake:${n}") flakeInputs;
  };
}
