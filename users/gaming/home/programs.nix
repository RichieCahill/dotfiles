{ pkgs, ... }:
{
  home.packages = with pkgs; [
    chromium
    vscode
    firefox
  ];
}
