let
  vars = import ../vars.nix;
in
{
  networking.firewall.allowedTCPPorts = [
    8989
  ];
  virtualisation.oci-containers.containers.signal_cli_rest_api = {
    image = "bbernhard/signal-cli-rest-api:latest";
    ports = [
      "8989:8080"
    ];
    volumes = [
      "${vars.docker_configs}/signal-cli-config:/home/.local/share/signal-cli"
    ];
    environment = {
      MODE = "json-rpc";
    };
    autoStart = true;
  };
}
