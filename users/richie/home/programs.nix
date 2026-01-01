{ pkgs, ... }:
{
  home.packages = with pkgs; [
    # cli
    bat
    btop
    busybox
    eza
    fd
    ffmpegthumbnailer
    fzf
    git
    gnupg
    imagemagick
    jq
    ncdu
    neofetch
    ouch
    p7zip
    poppler
    rar
    ripgrep
    starship
    tmux
    yazi
    zoxide
    # Home Assistant
    esphome
    # data recovery
    testdisk
    # system info
    hwloc
    lynis
    smartmontools
    usbutils
    # networking
    iperf3
    nmap
    # python
    poetry
    ruff
    uv
    # nodejs
    nodejs
    # Rust packages
    trunk
    wasm-pack
    cargo-watch
    cargo-generate
    cargo-audit
    cargo-update
    # nix
    nix-init
    nix-output-monitor
    nix-prefetch
    nix-tree
    nixfmt-rfc-style
    treefmt
  ];
}
