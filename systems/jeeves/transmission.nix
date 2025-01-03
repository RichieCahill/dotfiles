{ pkgs, ... }:
let
  vars = import ./vars.nix;
in
{
  environment.systemPackages = with pkgs; [
    transmission-rss
  ];
  services.transmission = {
    enable = true;
    package = pkgs.transmission_4;
    home = "${vars.media_docker_configs}/transmission";
    group = "users";
    openRPCPort = true;
    openPeerPorts = true;
    openFirewall = true;
    webHome = pkgs.flood-for-transmission;
    settings = {
      message-level = 2;
      incomplete-dir-enabled = true;
      incomplete-dir = "${vars.torrenting_transmission}/incomplete";
      download-dir = "${vars.torrenting_transmission}/download";
      download-queue-enabled = false;
      peer-limit-global = 10000;
      peer-limit-per-torrent = 100;
    };
  };
}
