{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    git
    my_python
  ];
}
