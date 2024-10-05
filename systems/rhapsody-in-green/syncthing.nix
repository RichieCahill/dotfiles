{    
  services.syncthing.settings.folders = {
    "notes" = {
      id = "l62ul-lpweo"; # cspell:disable-line
      path = "/home/richie/notes";
      devices = [
        "bob"
        "jeeves"
      ];
      fsWatcherEnabled = true;
    };
    "books" = {
      id = "6uppx-vadmy"; # cspell:disable-line
      path = "/home/richie/books";
      devices = [
        "bob"
        "jeeves"
        "phone"
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
      ];
      fsWatcherEnabled = true;
    };
    "music" = {
      id = "vprc5-3azqc"; # cspell:disable-line
      path = "/home/richie/music";
      devices = [
        "bob"
        "ipad"
        "jeeves"
        "phone"
      ];
      fsWatcherEnabled = true;
    };
    "projects" = {
      id = "vyma6-lqqrz"; # cspell:disable-line
      path = "/home/richie/projects";
      devices = [
        "bob"
        "jeeves"
      ];
      fsWatcherEnabled = true;
    };
  };
}
