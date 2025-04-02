{ lib, ... }:
let
  vars = import ../vars.nix;
in
{
  services.audiobookshelf.enable = true;
  systemd.services.audiobookshelf.serviceConfig.WorkingDirectory =
    lib.mkForce "${vars.docker_configs}/audiobookshelf";
  users.users.audiobookshelf.home = lib.mkForce "${vars.docker_configs}/audiobookshelf";
}
