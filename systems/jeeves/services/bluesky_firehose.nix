{
  pkgs,
  inputs,
  ...
}:
let
  commonEnv = {
    PYTHONPATH = "${inputs.self}";
    KAFKA_BOOTSTRAP_SERVERS = "localhost:9092";
    BLUESKY_FIREHOSE_TOPIC = "bluesky.firehose.posts";
  };
  commonServiceConfig = {
    Type = "simple";
    WorkingDirectory = "${inputs.self}";
    User = "richie";
    Group = "users";
    Restart = "on-failure";
    RestartSec = "10s";
    StandardOutput = "journal";
    StandardError = "journal";
    NoNewPrivileges = true;
    ProtectSystem = "strict";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ReadOnlyPaths = [ "${inputs.self}" ];
  };
in
{
  systemd.services.bluesky-firehose-topic-init = {
    description = "Create Kafka topic for Bluesky firehose";
    after = [ "apache-kafka.service" ];
    requires = [ "apache-kafka.service" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = pkgs.writeShellScript "create-bluesky-topic" ''
        ${pkgs.apacheKafka}/bin/kafka-topics.sh \
          --bootstrap-server localhost:9092 \
          --create \
          --if-not-exists \
          --topic bluesky.firehose.posts \
          --partitions 6 \
          --replication-factor 1
      '';
    };
  };

  systemd.services.bluesky-firehose-producer = {
    description = "Bluesky Jetstream to Kafka producer";
    after = [
      "network.target"
      "apache-kafka.service"
      "bluesky-firehose-topic-init.service"
    ];
    requires = [
      "apache-kafka.service"
      "bluesky-firehose-topic-init.service"
    ];
    wantedBy = [ "multi-user.target" ];

    environment = commonEnv;

    serviceConfig = commonServiceConfig // {
      ExecStart = "${pkgs.my_python}/bin/python -m python.data_science.firehose_producer";
    };
  };

  systemd.services.bluesky-firehose-consumer = {
    description = "Bluesky Kafka to PostgreSQL consumer";
    after = [
      "network.target"
      "apache-kafka.service"
      "bluesky-firehose-topic-init.service"
      "postgresql.service"
    ];
    requires = [
      "apache-kafka.service"
      "bluesky-firehose-topic-init.service"
      "postgresql.service"
    ];
    wantedBy = [ "multi-user.target" ];

    environment = commonEnv // {
      DATA_SCIENCE_DEV_DB = "data_science_dev";
      DATA_SCIENCE_DEV_USER = "richie";
      DATA_SCIENCE_DEV_HOST = "/run/postgresql";
      DATA_SCIENCE_DEV_PORT = "5432";
    };

    serviceConfig = commonServiceConfig // {
      ExecStart = "${pkgs.my_python}/bin/python -m python.data_science.firehose_consumer";
    };
  };
}
