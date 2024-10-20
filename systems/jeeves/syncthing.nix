let
  vars = import ./vars.nix;
in
{
  services.syncthing = {
    guiAddress = "192.168.90.40:8384";
    settings.folders = {
      "bob_temp" = {
        path = "${vars.storage_syncthing}/bob_temp";
        devices = [
          "jeeves"
        ];
        fsWatcherEnabled = true;
      };
      "notes" = {
        id = "l62ul-lpweo"; # cspell:disable-line
        path = vars.media_notes;
        devices = [
          "bob"
          "rhapsody-in-green"
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
      "rhapsody-in-green_temp" = {
        path = "${vars.storage_syncthing}/rhapsody-in-green_temp";
        devices = [
          "rhapsody-in-green"
        ];
        fsWatcherEnabled = true;
      };
    };
  };
}
