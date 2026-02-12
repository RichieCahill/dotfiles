{ pkgs, ... }:
{
  home.packages = with pkgs; [
    sweet-nova
    candy-icons
  ];
}
