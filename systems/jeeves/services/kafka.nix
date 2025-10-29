let
  vars = import ../vars.nix;
in
{
  services.apache-kafka = {
    enable = false;
    settings = {
      listeners = [ "PLAINTEXT://localhost:9092" ];
      "log.dirs" = [ vars.kafka ];
    };
  };
}
