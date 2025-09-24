{ pkgs, ... }:
{
  imports = [
    ./vscode
    ./kitty.nix
  ];

  home.packages = with pkgs; [
    candy-icons
    gimp
    obs-studio
    obsidian
    sweet-nova
    util-linux
    vlc
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
    prismlauncher
    tower-pixel-dungeon
  ];
}
