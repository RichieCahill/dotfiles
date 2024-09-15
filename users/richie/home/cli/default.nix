{
  imports = [
    ./direnv.nix
    ./fonts.nix
    ./git.nix
    ./zsh.nix
  ];

  programs.starship.enable = true;
}
