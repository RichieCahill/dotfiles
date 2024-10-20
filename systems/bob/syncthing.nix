{    
  services.syncthing.settings.folders = {
    "notes" = {
      id = "l62ul-lpweo"; # cspell:disable-line
      path = "/home/richie/notes";
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
    "projects" = {
      id = "vyma6-lqqrz"; # cspell:disable-line
      path = "/home/richie/projects";
      devices = [
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
    "vault" = {
      path = "/home/richie/vault";
      devices = [
        "rhapsody-in-green"
      ];
      fsWatcherEnabled = true;
    };
  };
}
