{ pkgs, ... }:
{
  programs.kitty = {
    enable = true;
    font.name = "IntoneMono Nerd Font";
    settings = {
      allow_remote_control = "yes";
      shell = "${pkgs.zsh}/bin/zsh";
      wayland_titlebar_color = "background";
      background_opacity = "0.75";
      tab_bar_edge = "top";
      tab_bar_style = "powerline";
      enabled_layouts = "splits";
    };
    keybindings = {
      "ctrl+alt+1" = "launch --type=tab --tab-title jeeves kitten ssh jeeves";
      "ctrl+alt+2" = "launch --type=tab --tab-title bob kitten ssh bob";
      "ctrl+alt+3" = "launch --type=tab --tab-title brain kitten ssh brain";
    };
    themeFile = "VSCode_Dark";
  };
}
