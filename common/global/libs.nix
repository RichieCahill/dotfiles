{ lib, pkgs, ... }:
let
  libPath = pkgs.lib.makeLibraryPath [
    pkgs.zlib
    pkgs.stdenv.cc.cc.lib
  ];
in
{
  programs.nix-ld = {
    enable = lib.mkDefault true;
    libraries = with pkgs; [
      acl
      attr
      bzip2
      curl
      glib
      libglvnd
      libmysqlclient
      libsodium
      libssh
      libxml2
      openssl
      stdenv.cc.cc
      stdenv.cc.cc.lib
      systemd
      util-linux
      xz
      zlib
      zlib-ng
      zstd
    ];
  };

  environment = {
    sessionVariables.LD_LIBRARY_PATH = lib.mkDefault libPath;
    variables.LD_LIBRARY_PATH = lib.mkDefault libPath;
  };
}
