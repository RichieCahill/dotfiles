{ pkgs, ... }:
let
  vars = import ../vars.nix;
in
{
  services.nix-serve = {
    package = pkgs.nix-serve-ng;
    enable = true;
    secretKeyFile = "${vars.secrets}/services/nix-cache/cache-priv-key.pem";
    openFirewall = true;
  };
}
