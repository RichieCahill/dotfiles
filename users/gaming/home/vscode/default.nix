{ pkgs, ... }:
{
  home.packages = with pkgs; [ nil ];

  programs.vscode = {
    enable = true;
    package = pkgs.vscode;
    mutableExtensionsDir = true;
  };
}
