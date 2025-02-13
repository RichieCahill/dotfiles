{
  pkgs,
  ...
}:
let
  vars = import ../vars.nix;
in
{
  systemd.services.filebrowser = {
    description = "filebrowser";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "richie";
      Group = "users";
      ExecStart = "${pkgs.filebrowser}/bin/filebrowser --root=/zfs --address=0.0.0.0 --database=${vars.media_docker_configs}/filebrowser/filebrowser.db";
      Restart = "on-failure";
    };
  };
}
