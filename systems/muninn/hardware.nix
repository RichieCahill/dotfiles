{ config, lib, modulesPath, ... }:

{
  imports = [ (modulesPath + "/installer/scan/not-detected.nix") ];

  boot = {
    initrd = {
      availableKernelModules = [
        "nvme"
        "xhci_pci"
        "thunderbolt"
        "usb_storage"
        "sd_mod"
      ];
      kernelModules = [ ];
      luks.devices."luks-root-pool-nvme-INTEL_SSDPEKKW256G7_BTPY63820XBH256D-part2" = {
        device = "/dev/disk/by-id/nvme-INTEL_SSDPEKKW256G7_BTPY63820XBH256D-part2";
        bypassWorkqueues = true;
        allowDiscards = true;
        keyFileSize = 4096;
        keyFile = "/dev/disk/by-id/usb-SanDisk_Ultra_T_C_4C530001020919102244-0:0";
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

    "/nix" = {
      device = "root_pool/nix";
      fsType = "zfs";
    };

    "/var" = {
      device = "root_pool/var";
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
