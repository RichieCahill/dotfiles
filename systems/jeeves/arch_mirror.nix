{ inputs, pkgs, ... }:
let
  vars = import ./vars.nix;
in
{
  virtualisation.oci-containers.containers.arch_mirror = {
    image = "ubuntu/apache2:latest";
    volumes = [
      "${../../users/richie/global/docker_templates}/file_server/sites/:/etc/apache2/sites-enabled/"
      "${vars.media_mirror}:/data"
    ];
    ports = [ "800:80" ];
    extraOptions = [ "--network=web" ];
    autoStart = true;
  };

  systemd.services.sync_mirror = {
    requires = [ "network-online.target" ];
    after = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    description = "validates startup";
    path = [ pkgs.rsync ];
    serviceConfig = {
      Environment = "MIRROR_DIR=${vars.media_mirror}/archlinux/";
      Type = "simple";
      ExecStart = "${inputs.system_tools.packages.x86_64-linux.default}/bin/sync_mirror";
    };
  };
}
