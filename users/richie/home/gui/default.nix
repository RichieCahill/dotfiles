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
    claude-code
    gparted
    jetbrains.datagrip
    master.antigravity-fhs
    proxychains
    # games
    dwarf-fortress
    tower-pixel-dungeon
    endless-sky
  ];
}
