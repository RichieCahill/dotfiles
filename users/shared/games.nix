{ pkgs, ... }:
{
  home.packages = with pkgs; [
    dolphin-emu
    dwarf-fortress
    endless-sky
    retroarch
    ryubing
    tower-pixel-dungeon
  ];
}
