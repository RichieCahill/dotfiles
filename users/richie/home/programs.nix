{ pkgs, inputs, ... }:
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
    p7zip
    poppler
    rar
    ripgrep
    starship
    tmux
    unzip
    yazi
    zoxide
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
    python312
    ruff
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
    nixpkgs-fmt
    inputs.system_tools.packages.x86_64-linux.default
  ];
}
