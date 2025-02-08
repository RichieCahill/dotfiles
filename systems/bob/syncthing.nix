{
  services.syncthing.settings.folders = {
    "dotfiles" = {
      path = "/home/richie/dotfiles";
      devices = [
        "jeeves"
        "rhapsody-in-green"
      ];
      fsWatcherEnabled = true;
    };
    "important" = {
      id = "4ckma-gtshs"; # cspell:disable-line
      path = "/home/richie/important";
      devices = [
        "phone"
        "jeeves"
        "rhapsody-in-green"
      ];
      fsWatcherEnabled = true;
    };
    "music" = {
      id = "vprc5-3azqc"; # cspell:disable-line
      path = "/home/richie/music";
      devices = [
        "ipad"
        "phone"
        "jeeves"
        "rhapsody-in-green"
      ];
      fsWatcherEnabled = true;
    };
  };
}
