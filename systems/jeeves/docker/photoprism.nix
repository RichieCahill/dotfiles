let
  vars = import ../vars.nix;
in
{


  virtualisation.oci-containers.containers = {
    photoprism = {
      image = "photoprism/photoprism:latest";
      ports = [ "2342:2342" ];
      volumes = [ 
        "${vars.media_docker_configs}/photoprism:/photoprism/storage"
        "${vars.storage_photos}/originals:/photoprism/originals"
        "${vars.storage_photos}/import:/photoprism/import"
      ];
      environment = {
        PHOTOPRISM_ADMIN_USER="admin";
        PHOTOPRISM_AUTH_MODE="password";
        PHOTOPRISM_DISABLE_TLS="false";
        PHOTOPRISM_DEFAULT_TLS="true";
        PHOTOPRISM_ORIGINALS_LIMIT="30000";
        PHOTOPRISM_HTTP_COMPRESSION="gzip";
        PHOTOPRISM_LOG_LEVEL="info";
        PHOTOPRISM_READONLY="false";
        PHOTOPRISM_EXPERIMENTAL="false";
        PHOTOPRISM_DISABLE_CHOWN="false";
        PHOTOPRISM_DISABLE_WEBDAV="false";
        PHOTOPRISM_DISABLE_SETTINGS="false";
        PHOTOPRISM_DISABLE_TENSORFLOW="false";
        PHOTOPRISM_DISABLE_FACES="false";
        PHOTOPRISM_DISABLE_CLASSIFICATION="false";
        PHOTOPRISM_DISABLE_VECTORS="false";
        PHOTOPRISM_DISABLE_RAW="false";
        PHOTOPRISM_RAW_PRESETS="false";
        PHOTOPRISM_SIDECAR_YAML="true";
        PHOTOPRISM_BACKUP_ALBUMS="true";
        PHOTOPRISM_BACKUP_DATABASE="true";
        PHOTOPRISM_BACKUP_SCHEDULE="daily";
        PHOTOPRISM_INDEX_SCHEDULE="";
        PHOTOPRISM_AUTO_INDEX="300";
        PHOTOPRISM_AUTO_IMPORT= "-1";
        PHOTOPRISM_DETECT_NSFW="false";
        PHOTOPRISM_UPLOAD_NSFW="true";
        PHOTOPRISM_DATABASE_DRIVER="mysql";
        PHOTOPRISM_DATABASE_SERVER="photoprism_mariadb:3306";
        PHOTOPRISM_DATABASE_NAME="photoprism";
        PHOTOPRISM_DATABASE_USER="photoprism";
        PHOTOPRISM_SITE_CAPTION="AI-Powered Photos App";
        PHOTOPRISM_SITE_DESCRIPTION="";
        PHOTOPRISM_SITE_AUTHOR="";
        PHOTOPRISM_UID="600";
        PHOTOPRISM_GID="600";
        # PHOTOPRISM_UMASK: 0000
      };
      environmentFiles = [/root/secrets/docker/photoprism];
      autoStart = true;
      dependsOn = [ "photoprism_mariadb" ];
      extraOptions = [ "--network=web" ];
    };
    photoprism_mariadb = {
      image = "mariadb:11";
      volumes = [ "${vars.media_database}/photoprism_mariadb:/var/lib/photoprism_mariadb" ];
      environment = {
        MARIADB_AUTO_UPGRADE = "1";
        MARIADB_INITDB_SKIP_TZINFO = "1";
        MARIADB_DATABASE = "photoprism";
        MARIADB_USER = "photoprism";
      };
      environmentFiles = [/root/secrets/docker/photoprism];
      cmd = [ "--innodb-buffer-pool-size=512M" "--transaction-isolation=READ-COMMITTED" "--character-set-server=utf8mb4" "--collation-server=utf8mb4_unicode_ci" "--max-connections=512" "--innodb-rollback-on-timeout=OFF" "--innodb-lock-wait-timeout=120" ];
      autoStart = true;
      extraOptions = [ "--network=web" ];
    };
  };
}
