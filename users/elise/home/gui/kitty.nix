{ pkgs, ... }:
{
  programs.kitty = {
    enable = true;
    font.name = "IntoneMono Nerd Font";
    settings = {
      allow_remote_control = "no";
      shell = "${pkgs.zsh}/bin/zsh";
      wayland_titlebar_color = "background";
    };
    themeFile = "VSCode_Dark";
  };
}
