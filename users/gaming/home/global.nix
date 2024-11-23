{ config, ... }:
{
  imports = [
    ./programs.nix
  ];

  programs = {
    home-manager.enable = true;
    git.enable = true;
  };

  home = {
    username = "gaming";
    homeDirectory = "/home/${config.home.username}";
    stateVersion = "24.05";
    sessionVariables = {
      FLAKE = "$HOME/Projects/dotfiles";
    };
  };
}
