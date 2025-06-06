{ config, ... }:
{
  nixpkgs.config.cudaSupport = true;

  services.xserver.videoDrivers = [ "nvidia" ];
  hardware = {
    nvidia = {
      modesetting.enable = true;
      powerManagement.enable = true;
      package = config.boot.kernelPackages.nvidiaPackages.beta;
      nvidiaSettings = true;
      open = false;
    };
    nvidia-container-toolkit.enable = true;
  };
}
