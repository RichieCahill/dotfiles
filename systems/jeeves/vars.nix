let
  zfs_media = "/zfs/media";
  zfs_storage = "/zfs/storage";
  zfs_scratch = "/zfs/scratch";
in
{
  inherit zfs_media zfs_storage zfs_scratch;
  database = "${zfs_media}/database";
  docker = "${zfs_media}/docker";
  docker_configs = "${zfs_media}/docker/configs";
  home_assistant = "${zfs_media}/home_assistant";
  notes = "${zfs_media}/notes";
  secrets = "${zfs_storage}/secrets";
  services = "${zfs_media}/services";
  share = "${zfs_media}/share";
  syncthing = "${zfs_storage}/syncthing";
  transmission = "${zfs_storage}/transmission";
  ollama = "${zfs_storage}/ollama";
  transmission_scratch = "${zfs_scratch}/transmission";
  kafka = "${zfs_scratch}/kafka";
}
