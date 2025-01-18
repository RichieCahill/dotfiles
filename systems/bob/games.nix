{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    osu-lazer-bin
    jellyfin-media-player
  ];
}
