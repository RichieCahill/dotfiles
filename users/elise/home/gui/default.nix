{ inputs, pkgs, ... }:
{
  imports = [
    "${inputs.self}/users/shared/comms.nix"
    "${inputs.self}/users/shared/games.nix"
    "${inputs.self}/users/shared/sweet.nix"
    ./kitty.nix
    ./vscode
  ];

  home.packages = with pkgs; [
    obs-studio
    obsidian
    vlc
    # graphics tools
    gimp3
    xcursorgen
    # browser
    chromium
    firefox
    # 3d modeling
    blender
    prusa-slicer
  ];
}
