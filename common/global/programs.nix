{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    git
    python313
  ];
}
