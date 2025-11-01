{ pkgs, ... }:
{
  imports = [
    ./vscode
    ./kitty.nix
  ];

  home.packages = with pkgs; [
    candy-icons
    obs-studio
    obsidian
    sweet-nova
    util-linux
    vlc
    # graphics tools
    gimp3
    xcursorgen
    # browser
    chromium
    firefox
    # communication
    discord-canary
    signal-desktop
    zoom-us
    # 3d modeling
    blender
    prusa-slicer
    # games
    dwarf-fortress
    endless-sky
    osu-lazer
    prismlauncher
    tower-pixel-dungeon
  ];
}
