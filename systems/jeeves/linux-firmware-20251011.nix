{ inputs, ... }:

let
  linuxFirmwareOverlay = final: prev: {
    linux-firmware =
      inputs.nixpkgs-linux-firmware-20251011.legacyPackages.${final.system}.linux-firmware;
  };
in
{
  nixpkgs.overlays = [ linuxFirmwareOverlay ];
}
