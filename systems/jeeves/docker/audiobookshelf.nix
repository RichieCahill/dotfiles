let
  vars = import ../vars.nix;
in
{
  virtualisation.oci-containers.containers.audiobookshelf = {
    image = "ghcr.io/advplyr/audiobookshelf:2.18.1";
    volumes = [
      "${vars.media_docker_configs}/audiobookshelf:/config"
      "${vars.media_docker_configs}/audiobookshelf:/metadata"
      "${vars.storage_library}/audiobooks:/audiobooks"
      "${vars.storage_library}/books:/books"
    ];
    environment = {
      TZ = "America/New_York";
    };
    extraOptions = [ "--network=web" ];
    autoStart = true;
  };
}
