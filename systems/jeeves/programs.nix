{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    filebot
    docker-compose
  ];
}
