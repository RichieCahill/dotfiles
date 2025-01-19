{
  system.autoUpgrade = {
    enable = true;
    flags = [ "--accept-flake-config" ];
    randomizedDelaySec = "1h";
    persistent = true;
    flake = "github:RichieCahill/dotfiles";
  };
}
