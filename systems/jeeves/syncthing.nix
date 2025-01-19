let
  vars = import ./vars.nix;
in
{
  services.syncthing = {
    guiAddress = "192.168.90.40:8384";
    settings.folders = {
      "dotfiles" = {
        path = "/home/richie/dotfiles";
        devices = [
          "bob"
          "rhapsody-in-green"
        ];
        fsWatcherEnabled = true;
      };
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
          "rhapsody-in-green"
          "davids-server"
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
      "vault" = {
        path = "/home/richie/vault";
        devices = [
          "rhapsody-in-green"
          "davids-server"
        ];
        fsWatcherEnabled = true;
      };
      "backup" = {
        path = "${vars.storage_syncthing}/backup";
        devices = [
          "davids-server"
        ];
        fsWatcherEnabled = true;
      };
      # 
      "davids-backup1" = {
        id = "8229p-8z3tm"; # cspell:disable-line
        path = "${vars.storage_syncthing}/davids_backups/1";
        devices = [
          "davids-server"
        ];
        fsWatcherEnabled = true;
        type = "receiveencrypted";
      };
      "davids-backup2" = {
        id = "iciw3-dp6ao"; # cspell:disable-line
        path = "${vars.storage_syncthing}/davids_backups/2";
        devices = [
          "davids-server"
        ];
        fsWatcherEnabled = true;
        type = "receiveencrypted";
      };
      "davids-backup3" = {
        id = "9si6m-bnkjb"; # cspell:disable-line
        path = "${vars.storage_syncthing}/davids_backups/3";
        devices = [
          "davids-server"
        ];
        fsWatcherEnabled = true;
        type = "receiveencrypted";
      };
      "davids-backup4" = {
        id = "qjyfy-uupj4"; # cspell:disable-line
        path = "${vars.storage_syncthing}/davids_backups/4";
        devices = [
          "davids-server"
        ];
        fsWatcherEnabled = true;
        type = "receiveencrypted";
      };
      "davids-backup5" = {
        id = "fm4h5-emsu2"; # cspell:disable-line
        path = "${vars.storage_syncthing}/davids_backups/5";
        devices = [
          "davids-server"
        ];
        fsWatcherEnabled = true;
        type = "receiveencrypted";
      };
    };
  };
}
