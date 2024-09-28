{ config, lib,  modulesPath, ... }:

{
  imports =[ (modulesPath + "/installer/scan/not-detected.nix") ];

  boot = {
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
        "luks-root-pool-wwn-0x500a0751e6c3c01e-part2" = {
          device = "/dev/disk/by-id/wwn-0x500a0751e6c3c01e-part2";
          bypassWorkqueues = true;
        };
        "luks-root-pool-wwn-0x500a0751e6c3c01c-part2" = {
          device = "/dev/disk/by-id/wwn-0x500a0751e6c3c01c-part2";
          bypassWorkqueues = true;
        };
        # Media pool
        "luks-media_pool-nvme-INTEL_SSDPEK1A118GA_BTOC14120V2J118B-part1" = {
          device = "/dev/disk/by-id/nvme-INTEL_SSDPEK1A118GA_BTOC14120V2J118B-part1";
          bypassWorkqueues = true;
          allowDiscards = true;
        };
        "luks-media_pool-nvme-INTEL_SSDPEK1A118GA_BTOC14120WAG118B-part1" = {
          device = "/dev/disk/by-id/nvme-INTEL_SSDPEK1A118GA_BTOC14120WAG118B-part1";
          bypassWorkqueues = true;
          allowDiscards = true;
        };
        "luks-media_pool-nvme-INTEL_SSDPE2ME012T4_CVMD5130000G1P2HGN-part1" = {
          device = "/dev/disk/by-id/nvme-INTEL_SSDPE2ME012T4_CVMD5130000G1P2HGN-part1";
          bypassWorkqueues = true;
          allowDiscards = true;
        };
        "luks-media_pool-nvme-INTEL_SSDPE2ME012T4_CVMD5130000U1P2HGN-part1" = {
          device = "/dev/disk/by-id/nvme-INTEL_SSDPE2ME012T4_CVMD5130000U1P2HGN-part1";
          bypassWorkqueues = true;
          allowDiscards = true;
        };
        # Torrenting pool
        "luks-torrenting_pool-wwn-0x5000cca264f080a3-part1".device = "/dev/disk/by-id/wwn-0x5000cca264f080a3-part1";
        "luks-torrenting_pool-wwn-0x5000cca298c33ae5-part1".device = "/dev/disk/by-id/wwn-0x5000cca298c33ae5-part1";
        # cspell:enable
      };
    };
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

    "/var" = {
      device = "root_pool/var";
      fsType = "zfs";
    };

    "/boot" = {
      device = "/dev/disk/by-id/wwn-0x500a0751e6c3c01e-part1";
      fsType = "vfat";
      options = [
        "fmask=0077"
        "dmask=0077"
      ];
    };
  };



  swapDevices = [
    {
      device = "/dev/disk/by-id/wwn-0x500a0751e6c3c01c-part3";
      randomEncryption = {
        enable = true; 
        allowDiscards = true;
      };
      priority = 10;
    }
    {
      device = "/dev/disk/by-id/wwn-0x500a0751e6c3c01e-part3";
      randomEncryption = {
        enable = true; 
        allowDiscards = true;
      };
      priority = 10;
    }
  ];

  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";
  hardware.cpu.amd.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;
}
