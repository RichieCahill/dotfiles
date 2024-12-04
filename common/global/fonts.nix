{ pkgs, ... }:
{
  fonts = {
    fontconfig.enable = true;
    enableDefaultPackages = true;
    packages = with pkgs; [
      nerd-fonts.roboto-mono
      nerd-fonts.intone-mono
      nerd-fonts.symbols-only
    ];
  };
}
