let
  vars = import ../vars.nix;
in
{
  services.open-webui = {
    stateDir = "${vars.services}/open_webui/";
    enable = true;
    openFirewall = true;
    environment = {
      ANONYMIZED_TELEMETRY = "False";
      DO_NOT_TRACK = "True";
      SCARF_NO_ANALYTICS = "True";
      OLLAMA_API_BASE_URL = "http://127.0.0.1:11434";
    };
  };
}
