{
  lib,
  pkgs,
  config,
  ...
}: {
  imports = [
    ./cli
    ./programs.nix
    ./ssh_config.nix
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
    username = lib.mkDefault "richie";
    homeDirectory = lib.mkDefault "/home/${config.home.username}";
    stateVersion = lib.mkDefault "24.05";
    sessionVariables = {
      FLAKE = "$HOME/Projects/dotfiles";
    };
  };
}
