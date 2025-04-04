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

        # Media pool
        "luks-media_pool-nvme-INTEL_SSDPEK1A118GA_BTOC14120V2J118B-part1" =
          makeLuksSSD "/dev/disk/by-id/nvme-INTEL_SSDPEK1A118GA_BTOC14120V2J118B-part1";
        "luks-media_pool-nvme-INTEL_SSDPEK1A118GA_BTOC14120WAG118B-part1" =
          makeLuksSSD "/dev/disk/by-id/nvme-INTEL_SSDPEK1A118GA_BTOC14120WAG118B-part1";
        "luks-media_pool-nvme-INTEL_SSDPE2ME012T4_CVMD5130000G1P2HGN-part1" =
          makeLuksSSD "/dev/disk/by-id/nvme-INTEL_SSDPE2ME012T4_CVMD5130000G1P2HGN-part1";
        "luks-media_pool-nvme-INTEL_SSDPE2ME012T4_CVMD5130000U1P2HGN-part1" =
          makeLuksSSD "/dev/disk/by-id/nvme-INTEL_SSDPE2ME012T4_CVMD5130000U1P2HGN-part1";

        # Scratch pool
        "luks-scratch-pool-ata-CT480BX500SSD1_2314E6C3C01C-part1" =
          makeLuksSSD "/dev/disk/by-id/ata-CT480BX500SSD1_2314E6C3C01C-part1";
        "luks-scratch-pool-ata-CT480BX500SSD1_2314E6C3C01E-part1" =
          makeLuksSSD "/dev/disk/by-id/ata-CT480BX500SSD1_2314E6C3C01E-part1";

        # Storage pool
        "luks-storage_pool-nvme-Samsung_SSD_970_EVO_Plus_2TB_S6S2NS0T834822N-part1" =
          makeLuksSSD "/dev/disk/by-id/nvme-Samsung_SSD_970_EVO_Plus_2TB_S6S2NS0T834822N-part1";
        "luks-storage_pool-nvme-Samsung_SSD_970_EVO_Plus_2TB_S6S2NS0T834817F-part1" =
          makeLuksSSD "/dev/disk/by-id/nvme-Samsung_SSD_970_EVO_Plus_2TB_S6S2NS0T834817F-part1";
        "luks-storage_pool-nvme-INTEL_MEMPEK1W016GA_PHBT828104DF016D-part1" =
          makeLuksSSD "/dev/disk/by-id/nvme-INTEL_MEMPEK1W016GA_PHBT828104DF016D-part1";
        "luks-storage_pool-nvme-INTEL_MEMPEK1W016GA_PHBT828105A8016D-part1" =
          makeLuksSSD "/dev/disk/by-id/nvme-INTEL_MEMPEK1W016GA_PHBT828105A8016D-part1";
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
