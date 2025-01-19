{ pkgs, ... }:
{
  boot = {
    kernelPackages = pkgs.linuxPackages_6_12;
    zfs.package = pkgs.zfs_2_3;
  };

  # rtkit is optional but recommended for pipewire
  security.rtkit.enable = true;

  services = {
    displayManager.sddm = {
      enable = true;
      wayland.enable = true;
    };

    desktopManager.plasma6.enable = true;

    xserver = {
      enable = true;
      xkb = {
        layout = "us";
        variant = "";
      };
    };

    pulseaudio.enable = false;

    pipewire = {
      enable = true;
      alsa.enable = true;
      alsa.support32Bit = true;
      pulse.enable = true;
      wireplumber.enable = true;
    };
  };
}
