{ pkgs, ... }:
{
  imports = [
    ./firefox
    ./vscode
  ];

  home.packages = with pkgs; [
    candy-icons
    chromium
    discord-canary
    gimp
    gparted
    mediainfo
    nemo
    nemo-fileroller
    obs-studio
    obsidian
    prismlauncher
    proxychains
    prusa-slicer
    signal-desktop
    sweet-nova
    util-linux
    vlc
    zoom-us
  ];
}
