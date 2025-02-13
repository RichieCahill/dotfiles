{ lib, ... }:
let
  vars = import ../vars.nix;
in
{
  services.audiobookshelf = {
    enable = true;
    openFirewall = true;
  };
  systemd.services.audiobookshelf.serviceConfig.WorkingDirectory =
    lib.mkForce "${vars.media_docker_configs}/audiobookshelf";
  users.users.audiobookshelf.home = lib.mkForce "${vars.media_docker_configs}/audiobookshelf";
}
