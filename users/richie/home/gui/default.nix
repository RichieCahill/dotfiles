{ pkgs, ... }:
{
  imports = [
    ./firefox.nix
    ./vscode
  ];

  home.packages = with pkgs; [
    candy-icons
    discord-canary
    gimp
    gparted
    mediainfo
    nemo
    nemo-fileroller
    obs-studio
    obsidian
    proxychains
    prusa-slicer
    signal-desktop
    sweet-nova
    util-linux
    vlc
    zoom-us
  ];
}
