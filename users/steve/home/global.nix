{ config, ... }:
{
  imports = [
    ./cli
    ./programs.nix
    ./ssh_config.nix
  ];

  programs = {
    home-manager.enable = true;
    git.enable = true;
  };

  home = {
    username = "steve";
    homeDirectory = "/home/${config.home.username}";
    stateVersion = "24.05";
    sessionVariables = {
      FLAKE = "$HOME/dotfiles";
    };
  };
}
