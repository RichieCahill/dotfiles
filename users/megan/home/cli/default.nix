{
  imports = [
    ./direnv.nix
    ./git.nix
    ./zsh.nix
  ];

  programs.starship.enable = true;
}
