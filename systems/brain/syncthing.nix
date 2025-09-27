{
  networking.firewall.allowedTCPPorts = [ 8384 ];

  services.syncthing = {
    overrideFolders = false;
    guiAddress = "192.168.90.35:8384";
    settings = {
      "dotfiles" = {
        path = "/home/richie/dotfiles";
        devices = [
          "jeeves"
          "bob"
          "rhapsody-in-green"
        ];
        fsWatcherEnabled = true;
      };
      "important" = {
        id = "4ckma-gtshs"; # cspell:disable-line
        path = "/home/richie/important";
        devices = [
          "bob"
          "jeeves"
          "phone"
          "rhapsody-in-green"
        ];
        fsWatcherEnabled = true;
      };
    };
  };
}
