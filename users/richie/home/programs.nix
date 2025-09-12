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
    python313
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
    inputs.system_tools.packages.x86_64-linux.default
  ];
}
