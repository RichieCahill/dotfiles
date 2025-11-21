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
        # Keychron keyboards
        KERNEL=="hidraw*", ATTRS{idVendor}=="3434", MODE="0660", GROUP="plugdev"
        SUBSYSTEM=="usb",  ATTR{idVendor}=="3434", MODE="0660", GROUP="plugdev"

        # Some boards use 32f0 as vendor id
        KERNEL=="hidraw*", ATTRS{idVendor}=="32f0", MODE="0660", GROUP="plugdev"
        SUBSYSTEM=="usb",  ATTR{idVendor}=="32f0", MODE="0660", GROUP="plugdev"

        # Keychron HID device permissions
        SUBSYSTEM=="usb", ATTR{idVendor}=="3434", MODE="0666"
        SUBSYSTEM=="hidraw", ATTRS{idVendor}=="3434", MODE="0666"

        # Keychron / QMK common bootloaders
        SUBSYSTEM=="usb", ATTR{idVendor}=="0483", ATTR{idProduct}=="df11", MODE="0666", GROUP="plugdev"
        SUBSYSTEM=="usb", ATTR{idVendor}=="03eb", MODE="0666", GROUP="plugdev"
        SUBSYSTEM=="usb", ATTR{idVendor}=="16c0", MODE="0666", GROUP="plugdev"
      '';
    };
  };
}
