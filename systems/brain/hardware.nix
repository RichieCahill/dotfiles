{
  config,
  lib,
  modulesPath,
  ...
}:
{
  imports = [ (modulesPath + "/installer/scan/not-detected.nix") ];

  boot = {
    initrd = {
      availableKernelModules = [
        "ahci"
        "ehci_pci"
        "nvme"
        "sd_mod"
        "usb_storage"
        "usbhid"
        "xhci_pci"
      ];
      kernelModules = [ ];
      luks.devices."luks-root-pool-nvme-Samsung_SSD_990_PRO_2TB_S7KHNJ0Y121613P-part2" = {
        device = "/dev/disk/by-id/nvme-Samsung_SSD_990_PRO_2TB_S7KHNJ0Y121613P-part2";
        bypassWorkqueues = true;
        allowDiscards = true;
      };
    };
    kernelModules = [ "kvm-intel" ];
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

    "/var" = {
      device = "root_pool/var";
      fsType = "zfs";
    };

    "/nix" = {
      device = "root_pool/nix";
      fsType = "zfs";
    };

    "/boot" = {
      device = "/dev/disk/by-uuid/12CE-A600";
      fsType = "vfat";
      options = [
        "fmask=0077"
        "dmask=0077"
      ];
    };
  };

  swapDevices = [ ];

  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";
  hardware.cpu.intel.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;
}
