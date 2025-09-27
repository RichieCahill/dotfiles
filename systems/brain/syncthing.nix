{
  services.syncthing.settings.folders = {
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
}
