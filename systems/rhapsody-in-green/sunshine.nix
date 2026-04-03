{ pkgs, ... }:
{
  services.sunshine = {
    enable = true;
    openFirewall = true;
    capSysAdmin = true;
  };
  environment.systemPackages = [ pkgs.kdePackages.libkscreen ];

  boot = {
    kernelParams = [
      "drm.edid_firmware=DP-4:edid/virtual-display.bin"
      "video=DP-4:e"
    ];
  };

  hardware.firmware = [
    (pkgs.runCommandLocal "virtual-display-edid"
      {
        compressFirmware = false;
      }
      ''
        mkdir -p $out/lib/firmware/edid
        cp ${./edid/virtual-display.bin} $out/lib/firmware/edid/virtual-display.bin
      ''
    )
  ];
}
