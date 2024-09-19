{    
  services.syncthing.settings.folders = {
    "notes" = {
      id = "l62ul-lpweo"; # cspell:disable-line
      path = "/home/richie/notes";
      devices = [
        "jeeves"
      ];
      fsWatcherEnabled = true;
    };
    "books" = {
      id = "6uppx-vadmy"; # cspell:disable-line
      path = "/home/richie/books";
      devices = [
        "phone"
        "jeeves"
      ];
      fsWatcherEnabled = true;
    };
    "important" = {
      id = "4ckma-gtshs"; # cspell:disable-line
      path = "/home/richie/important";
      devices = [
        "phone"
        "jeeves"
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
      ];
      fsWatcherEnabled = true;
    };
    "projects" = {
      id = "vyma6-lqqrz"; # cspell:disable-line
      path = "/home/richie/projects";
      devices = [
        "jeeves"
      ];
      fsWatcherEnabled = true;
    };
  };
}
