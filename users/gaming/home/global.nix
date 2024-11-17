{
  lib,
  pkgs,
  config,
  ...
}: {
  imports = [
    ./programs.nix
  ];

  nix = {
    package = lib.mkDefault pkgs.nix;
    settings = {
      experimental-features = [
        "nix-command"
        "flakes"
        "ca-derivations"
      ];
    };
  };

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
