let
  vars = import ./vars.nix;
in
{
  networking.firewall.allowedTCPPorts = [ 8384 ];

  services.syncthing = {
    overrideFolders = false;
    guiAddress = "192.168.90.40:8384";
    settings = {
      devices.davids-server.id = "7GXTDGR-AOXFW2O-K6J7NM3-XYZNRRW-AKHAFWM-GBOWUPQ-OA6JIWD-ER7RDQL"; # cspell:disable-line
      folders = {
        "dotfiles" = {
          path = "/home/richie/dotfiles";
          devices = [
            "bob"
            "brain"
            "rhapsody-in-green"
          ];
          fsWatcherEnabled = true;
        };
        "notes" = {
          id = "l62ul-lpweo"; # cspell:disable-line
          path = vars.notes;
          devices = [
            "rhapsody-in-green"
            {
              name = "davids-server";
              encryptionPasswordFile = "${vars.secrets}/services/syncthing/davids-server";
            }
          ];
          fsWatcherEnabled = true;
        };
        "important" = {
          id = "4ckma-gtshs"; # cspell:disable-line
          path = "${vars.syncthing}/important";
          devices = [
            "bob"
            "brain"
            "phone"
            "rhapsody-in-green"
          ];
          fsWatcherEnabled = true;
        };
        "music" = {
          id = "vprc5-3azqc"; # cspell:disable-line
          path = "${vars.syncthing}/music";
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
          path = "${vars.syncthing}/projects";
          devices = [
            "rhapsody-in-green"
          ];
          fsWatcherEnabled = true;
        };
        "rhapsody-in-green_temp" = {
          path = "${vars.syncthing}/rhapsody-in-green_temp";
          devices = [
            "rhapsody-in-green"
          ];
          fsWatcherEnabled = true;
        };
        "vault" = {
          path = "/home/richie/vault";
          devices = [
            "rhapsody-in-green"
            {
              name = "davids-server";
              encryptionPasswordFile = "${vars.secrets}/services/syncthing/davids-server";
            }
          ];
          fsWatcherEnabled = true;
        };
        "backup" = {
          path = "${vars.syncthing}/backup";
          devices = [
            {
              name = "davids-server";
              encryptionPasswordFile = "${vars.secrets}/services/syncthing/davids-server";
            }
          ];
          fsWatcherEnabled = true;
        };
        #
        "davids-backup1" = {
          id = "8229p-8z3tm"; # cspell:disable-line
          path = "${vars.syncthing}/davids_backups/1";
          devices = [
            "davids-server"
          ];
          fsWatcherEnabled = true;
          type = "receiveencrypted";
        };
        "davids-backup2" = {
          id = "iciw3-dp6ao"; # cspell:disable-line
          path = "${vars.syncthing}/davids_backups/2";
          devices = [
            "davids-server"
          ];
          fsWatcherEnabled = true;
          type = "receiveencrypted";
        };
        "davids-backup3" = {
          id = "9si6m-bnkjb"; # cspell:disable-line
          path = "${vars.syncthing}/davids_backups/3";
          devices = [
            "davids-server"
          ];
          fsWatcherEnabled = true;
          type = "receiveencrypted";
        };
        "davids-backup4" = {
          id = "qjyfy-uupj4"; # cspell:disable-line
          path = "${vars.syncthing}/davids_backups/4";
          devices = [
            "davids-server"
          ];
          fsWatcherEnabled = true;
          type = "receiveencrypted";
        };
        "davids-backup5" = {
          id = "fm4h5-emsu2"; # cspell:disable-line
          path = "${vars.syncthing}/davids_backups/5";
          devices = [
            "davids-server"
          ];
          fsWatcherEnabled = true;
          type = "receiveencrypted";
        };
      };
    };
  };
}
