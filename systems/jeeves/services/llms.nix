let
  vars = import ../vars.nix;
in
{
  services.ollama = {
    user = "ollama";
    enable = true;
    host = "0.0.0.0";
    syncModels = true;
    loadModels = [
      "codellama:7b"
      "deepscaler:1.5b"
      "deepseek-r1:14b"
      "deepseek-r1:32b"
      "deepseek-r1:8b"
      "devstral-small-2:24b"
      "functiongemma:270m"
      "gemma3:12b"
      "gemma3:27b"
      "gpt-oss:120b"
      "gpt-oss:20b"
      "llama3.1:70b"
      "llama3.1:8b"
      "llama3.2:1b"
      "llama3.2:3b"
      "magistral:24b"
      "ministral-3:14b"
      "nemotron-3-nano:30b"
      "qwen3-coder:30b"
      "qwen3-vl:32b"
      "qwen3:14b"
      "qwen3:30b"
    ];
    models = vars.ollama;
    openFirewall = true;
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
