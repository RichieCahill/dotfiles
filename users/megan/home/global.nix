{ config, ... }:
{
  imports = [
    ./cli
    ./programs.nix
  ];

  programs = {
    home-manager.enable = true;
    git.enable = true;
  };

  home = {
    username = "megan";
    homeDirectory = "/home/${config.home.username}";
    stateVersion = "24.05";
  };
}
