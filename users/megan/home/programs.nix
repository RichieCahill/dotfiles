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
  ];
}
