{ pkgs, ... }:
{
  home.packages = with pkgs; [
    # python
    poetry
    python313
    ruff
    # nix
    nix-init
    nix-output-monitor
    nix-prefetch
    nix-tree
    nixfmt-rfc-style
    treefmt
  ];
}
