{ config, lib, modulesPath, ... }:
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
        # Storage pool
        "luks-storage_pool-nvme-Samsung_SSD_970_EVO_Plus_2TB_S6S2NS0T834822N-part1" = {
          device = "/dev/disk/by-id/nvme-Samsung_SSD_970_EVO_Plus_2TB_S6S2NS0T834822N-part1";
          bypassWorkqueues = true;
          allowDiscards = true;
        };
        "luks-storage_pool-nvme-Samsung_SSD_970_EVO_Plus_2TB_S6S2NS0T834817F-part1" = {
          device = "/dev/disk/by-id/nvme-Samsung_SSD_970_EVO_Plus_2TB_S6S2NS0T834817F-part1";
          bypassWorkqueues = true;
          allowDiscards = true;
        };
        "luks-storage_pool-nvme-INTEL_MEMPEK1W016GA_PHBT828104DF016D-part1" = {
          device = "/dev/disk/by-id/nvme-INTEL_MEMPEK1W016GA_PHBT828104DF016D-part1";
          bypassWorkqueues = true;
          allowDiscards = true;
        };
        "luks-storage_pool-nvme-INTEL_MEMPEK1W016GA_PHBT828105A8016D-part1" = {
          device = "/dev/disk/by-id/nvme-INTEL_MEMPEK1W016GA_PHBT828105A8016D-part1";
          bypassWorkqueues = true;
          allowDiscards = true;
        };
        "luks-storage_pool-wwn-0x5000cca23bc438dd-part1".device = "/dev/disk/by-id/wwn-0x5000cca23bc438dd-part1";
        "luks-storage_pool-wwn-0x5000cca23bd035f5-part1".device = "/dev/disk/by-id/wwn-0x5000cca23bd035f5-part1";
        "luks-storage_pool-wwn-0x5000cca23bd00ad6-part1".device = "/dev/disk/by-id/wwn-0x5000cca23bd00ad6-part1";
        "luks-storage_pool-wwn-0x5000cca23bcf313e-part1".device = "/dev/disk/by-id/wwn-0x5000cca23bcf313e-part1";
        "luks-storage_pool-wwn-0x5000cca23bcdf3b8-part1".device = "/dev/disk/by-id/wwn-0x5000cca23bcdf3b8-part1";
        "luks-storage_pool-wwn-0x5000cca23bd02746-part1".device = "/dev/disk/by-id/wwn-0x5000cca23bd02746-part1";
        "luks-storage_pool-wwn-0x5000cca23bcf9f89-part1".device = "/dev/disk/by-id/wwn-0x5000cca23bcf9f89-part1";
        "luks-storage_pool-wwn-0x5000cca23bd00ae9-part1".device = "/dev/disk/by-id/wwn-0x5000cca23bd00ae9-part1";
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

    fileSystems."/nix" =
    { device = "root_pool/nix";
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
