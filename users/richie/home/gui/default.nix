{ inputs, pkgs, ... }:
{
  imports = [
    "${inputs.self}/users/shared/comms.nix"
    "${inputs.self}/users/shared/games.nix"
    "${inputs.self}/users/shared/sweet.nix"
    ./firefox
    ./kitty.nix
    ./vscode
  ];

  home.packages = with pkgs; [
    gimp
    mediainfo
    obs-studio
    obsidian
    prismlauncher
    prusa-slicer
    vlc
    # browser
    chromium
    # dev tools
    claude-code
    gparted
    jetbrains.datagrip
    antigravity-fhs
    proxychains
    opencode
  ];
}
