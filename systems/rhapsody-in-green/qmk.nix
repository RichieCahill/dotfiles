{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    qmk
    vial
  ];

  services = {
    udev = {
      packages = [ pkgs.qmk-udev-rules ];
      extraRules = ''
        # Keychron / QMK common bootloaders
        SUBSYSTEM=="usb", ATTR{idVendor}=="0483", ATTR{idProduct}=="df11", MODE="0666", GROUP="plugdev"
        SUBSYSTEM=="usb", ATTR{idVendor}=="03eb", MODE="0666", GROUP="plugdev"
        SUBSYSTEM=="usb", ATTR{idVendor}=="16c0", MODE="0666", GROUP="plugdev"
      '';
    };
  };
}
