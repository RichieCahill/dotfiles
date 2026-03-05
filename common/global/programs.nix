{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    git
    my_python
    ds_python
  ];
}
