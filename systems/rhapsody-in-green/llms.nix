{
  services = {
    ollama = {
      user = "ollama";
      enable = true;
      host = "127.0.0.1";
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
    };
    open-webui = {
      enable = true;
      host = "127.0.0.1";
      environment = {
        ANONYMIZED_TELEMETRY = "False";
        DO_NOT_TRACK = "True";
        SCARF_NO_ANALYTICS = "True";
        OLLAMA_API_BASE_URL = "http://127.0.0.1:11434";
        WEBUI_AUTH = "False";
      };
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
