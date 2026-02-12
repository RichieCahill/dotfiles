{ pkgs, ... }:
{
  home.packages = with pkgs; [
    discord-canary
    signal-desktop
    zoom-us
  ];
}
