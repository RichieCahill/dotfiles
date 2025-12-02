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
    gimp
    mediainfo
    obs-studio
    obsidian
    prismlauncher
    prusa-slicer
    sweet-nova
    util-linux
    vlc
    # comms
    discord-canary
    signal-desktop
    zoom-us
    # dev tools
    jetbrains.datagrip
    proxychains
    master.antigravity-fhs
    gparted
    # games
    dwarf-fortress
    tower-pixel-dungeon
    endless-sky
  ];
}
