let
  vars = import ../vars.nix;
in
{
  services.apache-kafka = {
    enable = true;
    settings = {
      listeners = [ "PLAINTEXT://localhost:9092" ];
      "log.dirs" = [ vars.kafka ];
    };
  };
}
