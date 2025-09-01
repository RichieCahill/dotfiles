let
  vars = import ../vars.nix;
in
{
  services = {
    ollama = {
      user = "ollama";
      enable = true;
      host = "0.0.0.0";
      loadModels = [
        "codellama:7b"
        "deepseek-r1:14b"
        "deepseek-r1:32b"
        "deepseek-r1:8b"
        "gemma3:12b"
        "gemma3:27b"
        "gpt-oss:120b"
        "gpt-oss:20b"
        "qwen3:14b"
        "qwen3:30b"
      ];
      models = vars.ollama;
      openFirewall = true;
    };
  };
  systemd.services = {
    ollama.serviceConfig = {
      Nice = 19;
      IOSchedulingPriority = 7;
    };
    ollama-model-loader.serviceConfig = {
      Nice = 19;
      CPUWeight = 50;
      IOSchedulingClass = "idle";
      IOSchedulingPriority = 7;
    };
  };
}
