{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    mangohud
    steam-run
  ];
  hardware.steam-hardware.enable = true;

  programs = {
    gamemode.enable = true;
    steam = {
      enable = true;
      gamescopeSession.enable = true;
      remotePlay.openFirewall = true;
      localNetworkGameTransfers.openFirewall = true;
      protontricks.enable = true;
      extraCompatPackages = with pkgs; [ proton-ge-bin ];
      extest.enable = true;
    };
    gamescope = {
      enable = true;
      capSysNice = true;
    };
  };
}
