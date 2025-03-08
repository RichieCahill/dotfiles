{ pkgs, ... }:
let
  vars = import ../vars.nix;
in
{
  services.transmission = {
    enable = true;
    package = pkgs.transmission_4;
    webHome = pkgs.flood-for-transmission;
    home = "${vars.media_services}/transmission";
    openPeerPorts = true;
    openRPCPort = true;
    downloadDirPermissions = "770";
    settings = {
      bind-address-ipv4 = "192.168.95.14";
      cache-size-mb = 0;
      download-dir = "${vars.torrenting_transmission}/complete";
      download-queue-enabled = false;
      incomplete-dir = "${vars.torrenting_transmission}/incomplete";
      incomplete-dir-enabled = true;
      message-level = 3;
      peer-port = 51413;
      rpc-bind-address = "0.0.0.0";
      rpc-host-whitelist = "127.0.0.1,192.168.90.40";
      rpc-host-whitelist-enabled = true;
      rpc-port = 9091;
      rpc-whitelist-enabled = true;
      rpc-whitelist = "127.0.0.1,192.168.90.49";
      seed-queue-enabled = false;
    };
  };
}
