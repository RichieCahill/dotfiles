{ pkgs, ... }:
{
  services.nix-serve = {
    package = pkgs.nix-serve-ng;
    enable = true;
    openFirewall = true;
  };
}
