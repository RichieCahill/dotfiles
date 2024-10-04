let
  vars = import ./vars.nix;
in
{
  services.syncthing = {
    guiAddress = "192.168.90.40:8384";
    settings.folders = {
      "notes" = {
        id = "l62ul-lpweo"; # cspell:disable-line
        path = vars.media_notes;
        devices = [
          "bob"
          "rhapsody-in-green"
        ];
        fsWatcherEnabled = true;
      };
      "books" = {
        id = "6uppx-vadmy"; # cspell:disable-line
        path = "${vars.storage_syncthing}/books";
        devices = [
          "bob"
          "rhapsody-in-green"
          "phone"
        ];
        fsWatcherEnabled = true;
      };
      "important" = {
        id = "4ckma-gtshs"; # cspell:disable-line
        path = "${vars.storage_syncthing}/important";
        devices = [
          "bob"
          "rhapsody-in-green"
          "phone"
        ];
        fsWatcherEnabled = true;
      };
      "music" = {
        id = "vprc5-3azqc"; # cspell:disable-line
        path = "${vars.storage_syncthing}/music";
        devices = [
          "bob"
          "rhapsody-in-green"
          "ipad"
          "phone"
        ];
        fsWatcherEnabled = true;
      };
      "projects" = {
        id = "vyma6-lqqrz"; # cspell:disable-line
        path = "${vars.storage_syncthing}/projects";
        devices = [
          "bob"
          "rhapsody-in-green"
        ];
        fsWatcherEnabled = true;
      };
    };
  };
}
