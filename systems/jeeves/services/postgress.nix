{ pkgs, ... }:
let
  vars = import ../vars.nix;
in
{
  networking.firewall.allowedTCPPorts = [ 5432 ];

  services.postgresql = {
    enable = true;
    package = pkgs.postgresql_17_jit;
    enableTCPIP = true;
    enableJIT = true;
    dataDir = "${vars.database}/postgres";

    authentication = pkgs.lib.mkOverride 10 ''

      # admins
      local all  postgres   trust
      host  all  postgres   127.0.0.1/32    trust
      host  all  postgres   ::1/128         trust 

      local all  richie   trust
      host  all  richie   127.0.0.1/32    trust
      host  all  richie   ::1/128         trust 
      host  all  richie   192.168.90.1/24 trust
      host  all  richie   192.168.99.1/24 trust


      #type database DBuser origin-address auth-method
      local hass     hass      trust

      # ipv4
      host  hass     hass       192.168.90.1/24 trust
      host  hass     hass       127.0.0.1/32 trust

      # ipv6
      host hass      hass     ::1/128         trust
    '';

    identMap = ''
      # ArbitraryMapName systemUser DBUser
        superuser_map      root      postgres
        superuser_map      postgres  postgres
        # Let other names login as themselves
        superuser_map      richie    postgres
        superuser_map      hass      hass
    '';
    ensureUsers = [
      {
        name = "postgres";
        ensureClauses = {
          superuser = true;
          login = true;
          createrole = true;
          createdb = true;
          replication = true;
        };
      }
      {
        name = "richie";
        ensureDBOwnership = true;
        ensureClauses = {
          superuser = true;
          login = true;
          createrole = true;
          createdb = true;
          replication = true;
        };
      }
      {
        name = "hass";
        ensureDBOwnership = true;
        ensureClauses = {
          login = true;
          createrole = true;
          createdb = true;
          replication = true;
        };
      }
    ];
    ensureDatabases = [
      "hass"
      "mxr_dev"
      "mxr_prod"
      "richie"
    ];
    # Thank you NotAShelf
    # https://github.com/NotAShelf/nyx/blob/d407b4d6e5ab7f60350af61a3d73a62a5e9ac660/modules/core/roles/server/system/services/databases/postgresql.nix#L74
    settings = {
      # Connectivity;
      max_connections = 100;
      superuser_reserved_connections = 3;

      # Memory Settings;
      shared_buffers = "1024 MB";
      work_mem = "32 MB";
      maintenance_work_mem = "320 MB";
      huge_pages = "off";
      effective_cache_size = "2 GB";
      effective_io_concurrency = 100; # concurrent IO only really activated if OS supports posix_fadvise function;
      random_page_cost = 1.25; # speed of random disk access relative to sequential access (1.0);

      # Monitoring;
      shared_preload_libraries = "pg_stat_statements,auto_explain"; # per statement resource usage stats & log explain statements for slow queries
      track_io_timing = "on"; # measure exact block IO times;
      track_functions = "pl"; # track execution times of pl-language procedures if any;
      # Replication;
      wal_level = "replica"; # consider using at least "replica";
      max_wal_senders = 0;
      synchronous_commit = "on";

      # Checkpointing: ;
      checkpoint_timeout = "15 min";
      checkpoint_completion_target = 0.9;
      max_wal_size = "1024 MB";
      min_wal_size = "512 MB";

      # WAL writing;
      wal_compression = "on";
      wal_buffers = -1; # auto-tuned by Postgres till maximum of segment size (16MB by default);
      wal_writer_delay = "200ms";
      wal_writer_flush_after = "1MB";

      # Background writer;
      bgwriter_delay = "200ms";
      bgwriter_lru_maxpages = 100;
      bgwriter_lru_multiplier = 2.0;
      bgwriter_flush_after = 0;

      # Parallel queries: ;
      max_worker_processes = 6;
      max_parallel_workers_per_gather = 3;
      max_parallel_maintenance_workers = 3;
      max_parallel_workers = 6;
      parallel_leader_participation = "on";

      # Advanced features ;
      enable_partitionwise_join = "on";
      enable_partitionwise_aggregate = "on";
      jit = "on";

      jit_above_cost = 100000;
      jit_inline_above_cost = 150000;
      jit_optimize_above_cost = 500000;

      # log slow queries
      log_min_duration_statement = 100;
      "auto_explain.log_min_duration" = 100;

      # logging configuration
      log_connections = true;
      log_statement = "all";
      logging_collector = true;
      log_disconnections = true;
    };
  };
}
