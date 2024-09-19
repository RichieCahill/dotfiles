{ pkgs, ... }:
{
  services.pcscd.enable = true;

  environment.systemPackages = [ pkgs.yubioath-flutter ];
}
