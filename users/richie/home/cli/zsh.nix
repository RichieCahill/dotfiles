{
  programs.zsh = {
    enable = true;
    syntaxHighlighting.enable = true;
    history.size = 10000;
    oh-my-zsh = {
      enable = true;
      plugins = [
        "git"
        "docker"
        "docker-compose"
        "colored-man-pages"
        "rust"
        "systemd"
        "tmux"
        "ufw"
        "z"
      ];
    };
    shellAliases = {
      "lrt" = "eza --icons -lsnew";
      "ls" = "eza";
      "ll" = "eza --long --group";
      "la" = "eza --all";

      "rspace" = "'for f in *\ *; do mv \"$f\" \"\${f// /_}\"; done'";
      "rebuild" = "sudo nixos-rebuild switch --flake /home/richie/dotfiles#$HOST";
      "nix-test" = "nixos-rebuild test --flake /home/richie/dotfiles";
    };
  };
}
