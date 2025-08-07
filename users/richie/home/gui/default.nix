{ pkgs, ... }:
{
  imports = [
    ./firefox
    ./vscode
    ./kitty.nix
  ];

  home.packages = with pkgs; [
    candy-icons
    chromium
    discord-canary
    gimp
    gparted
    jetbrains.datagrip
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
    # games
    dwarf-fortress
    tower-pixel-dungeon
    endless-sky 
  ];
}
