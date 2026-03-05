{
  services.ollama = {
    user = "ollama";
    enable = true;
    host = "127.0.0.1";
    syncModels = true;
    loadModels = [
      "deepscaler:1.5b"
      "deepseek-r1:8b"
      "gemma3:12b"
      "gemma3:27b"
      "gpt-oss:20b"
      "lfm2:24b"
      "qwen3:14b"
      "qwen3.5:35b"
    ];
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
