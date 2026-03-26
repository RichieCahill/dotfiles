let
  vars = import ../vars.nix;
in
{
  services.apache-kafka = {
    enable = true;
    settings = {
      listeners = [ "PLAINTEXT://localhost:9092" ];
      "log.dirs" = [ vars.kafka ];
      "num.partitions" = 6;
      "default.replication.factor" = 1;
      "log.retention.hours" = 168;
      "log.retention.bytes" = 10737418240;
      "log.segment.bytes" = 1073741824;
      "log.cleanup.policy" = "delete";
      "auto.create.topics.enable" = false;
    };
  };
}
