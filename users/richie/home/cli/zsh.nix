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

      "rebuild" = "sudo nixos-rebuild switch --flake $HOME/dotfiles#$HOST";
      "rebuild_backup" =
        "sudo nixos-rebuild switch --flake $HOME/dotfiles#$HOST --option substituters 'https://nix-community.cachix.org' --option trusted-public-keys 'cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY='";
    };
  };
}
