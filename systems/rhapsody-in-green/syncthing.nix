{
  services.syncthing.settings.folders = {
    "dotfiles" = {
      path = "/home/richie/dotfiles";
      devices = [
        "jeeves"
        "bob"
      ];
      fsWatcherEnabled = true;
    };
    "notes" = {
      id = "l62ul-lpweo"; # cspell:disable-line
      path = "/home/richie/notes";
      devices = [
        "jeeves"
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
        "jeeves"
      ];
      fsWatcherEnabled = true;
    };
    rhapsody-in-temp = {
      id = "rhapsody-in-green_temp";
      path = "/home/richie/temp";
      devices = [
        "jeeves"
      ];
      fsWatcherEnabled = true;
    };
    "vault" = {
      path = "/home/richie/vault";
      devices = [
        "jeeves"
      ];
      fsWatcherEnabled = true;
    };
  };
}
