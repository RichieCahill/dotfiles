{ pkgs, ... }:
{
  home.packages = with pkgs; [
    # cli
    bat
    btop
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
    unzip
    yazi
    zoxide
    # Home Assistant
    esphome
    # data recovery
    testdisk
    # system info
    hwloc
    lynis
    pciutils
    smartmontools
    usbutils
    # networking
    iperf3
    nmap
    wget
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
    # cpp
    clang-tools
    clang_20
    # nix
    nix-init
    nix-output-monitor
    nix-prefetch
    nix-tree
    nixfmt
    treefmt
  ];
}
