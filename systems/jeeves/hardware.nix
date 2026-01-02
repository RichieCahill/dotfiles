{
  config,
  lib,
  modulesPath,
  ...
}:
let
  makeLuksDevice = device: {
    inherit device;
    keyFileSize = 4096;
    keyFile = "/dev/disk/by-id/usb-XIAO_USB_Drive_24587CE29074-0:0";
    fallbackToPassword = true;
  };
  makeLuksSSD =
    device:
    (makeLuksDevice device)
    // {
      bypassWorkqueues = true;
      allowDiscards = true;
    };
in
{
  imports = [ (modulesPath + "/installer/scan/not-detected.nix") ];

  boot = {
    loader = {
      grub = {
        enable = true;
        zfsSupport = true;
        efiSupport = true;
        mirroredBoots = [
          {
            devices = [ "nodev" ];
            path = "/boot0";
          }
          {
            devices = [ "nodev" ];
            path = "/boot1";
          }
        ];
      };
      efi.canTouchEfiVariables = true;
    };
    initrd = {
      availableKernelModules = [
        "ahci"
        "mpt3sas"
        "nvme"
        "sd_mod"
        "sr_mod"
        "usb_storage"
        "usbhid"
        "xhci_pci"
      ];
      kernelModules = [ ];
      luks.devices = {
        # cspell:disable
        # Root pool
        "luks-root-pool-wwn-0x55cd2e4150f01519-part2" =
          makeLuksSSD "/dev/disk/by-id/wwn-0x55cd2e4150f01519-part2";
        "luks-root-pool-wwn-0x55cd2e4150f01556-part2" =
          makeLuksSSD "/dev/disk/by-id/wwn-0x55cd2e4150f01556-part2";

        # Storage pool
        "luks-storage_pool-wwn-0x5000cca23bc438dd-part1" =
          makeLuksDevice "/dev/disk/by-id/wwn-0x5000cca23bc438dd-part1";
        "luks-storage_pool-wwn-0x5000cca23bd035f5-part1" =
          makeLuksDevice "/dev/disk/by-id/wwn-0x5000cca23bd035f5-part1";
        "luks-storage_pool-wwn-0x5000cca23bd00ad6-part1" =
          makeLuksDevice "/dev/disk/by-id/wwn-0x5000cca23bd00ad6-part1";
      };
    };

    zfs.extraPools = [
      "media"
      "scratch"
      "storage"
    ];

    kernelModules = [ "kvm-amd" ];
    extraModulePackages = [ ];
  };

  fileSystems = {
    "/" = lib.mkDefault {
      device = "root_pool/root";
      fsType = "zfs";
    };

    "/home" = {
      device = "root_pool/home";
      fsType = "zfs";
    };

    "/nix" = {
      device = "root_pool/nix";
      fsType = "zfs";
    };

    "/var" = {
      device = "root_pool/var";
      fsType = "zfs";
    };

    "/boot0" = {
      device = "/dev/disk/by-id/wwn-0x55cd2e4150f01556-part1";
      fsType = "vfat";
      options = [
        "fmask=0077"
        "dmask=0077"
      ];
    };
    "/boot1" = {
      device = "/dev/disk/by-id/wwn-0x55cd2e4150f01519-part1";
      fsType = "vfat";
      options = [
        "fmask=0077"
        "dmask=0077"
      ];
    };
  };

  swapDevices = [ ];

  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";
  hardware.cpu.amd.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;
}
