let
  zfs_media = "/zfs/media";
  zfs_storage = "/zfs/storage";
  zfs_torrenting = "/zfs/torrenting";
in
{
  inherit zfs_media zfs_storage zfs_torrenting;
  # media
  media_database = "${zfs_media}/database";
  media_docker = "${zfs_media}/docker";
  media_docker_configs = "${zfs_media}/docker/configs";
  media_mirror = "${zfs_media}/mirror";
  media_share = "${zfs_media}/share";
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
  # torrenting
  torrenting_qbit = "${zfs_torrenting}/qbit";
  torrenting_qbitvpn = "${zfs_torrenting}/qbitvpn";
}
