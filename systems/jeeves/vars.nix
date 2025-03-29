let
  zfs_media = "/zfs/media";
  zfs_storage = "/zfs/storage";
in
{
  inherit zfs_media zfs_storage;
  # media
  media_database = "${zfs_media}/database";
  media_docker = "${zfs_media}/docker";
  media_docker_configs = "${zfs_media}/docker/configs";
  media_mirror = "${zfs_media}/mirror";
  media_share = "${zfs_media}/share";
  media_services = "${zfs_media}/services";
  media_notes = "${zfs_media}/notes";
  media_plex = "${zfs_media}/plex";
  media_home_assistant = "${zfs_media}/home_assistant";
  # storage
  storage_main = "${zfs_storage}/main";
  storage_photos = "${zfs_storage}/photos";
  storage_plex = "${zfs_storage}/plex";
  storage_secrets = "${zfs_storage}/secrets";
  storage_syncthing = "${zfs_storage}/syncthing";
  storage_library = "${zfs_storage}/library";
  storage_qbitvpn = "${zfs_storage}/qbitvpn";
  storage_transmission = "${zfs_storage}/transmission";

}
