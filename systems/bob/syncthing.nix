{    
  services.syncthing.settings.folders = {
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
    "temp" = {
      id = "bob_temp";
      path = "/home/richie/temp";
      devices = [
        "jeeves"
      ];
      fsWatcherEnabled = true;
    };
  };
}
