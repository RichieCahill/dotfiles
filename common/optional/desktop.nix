{
  imports = [
    ./desktop_kernel.nix
    ./pipewire.nix
  ];
  services = {
    desktopManager.plasma6.enable = true;
    xserver = {
      enable = true;
      xkb = {
        layout = "us";
        variant = "";
      };
    };
  };
}
