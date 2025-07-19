{
  system.autoUpgrade = {
    enable = true;
    flags = [ "--accept-flake-config" ];
    randomizedDelaySec = "1h";
    persistent = true;
    flake = "github:RichieCahill/dotfiles";
    allowReboot = true;
    dates = "Sat *-*-* 06:00:00";
  };
}
