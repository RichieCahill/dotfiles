{
  services.ollama = {
    user = "ollama";
    host = "0.0.0.0";
    enable = true;

    syncModels = true;
    loadModels = [
      "codellama:7b"
      "deepscaler:1.5b"
      "deepseek-r1:8b"
      "deepseek-r1:14b"
      "deepseek-r1:32b"
      "devstral-small-2:24b"
      "functiongemma:270m"
      "gemma3:12b"
      "gemma3:27b"
      "gpt-oss:20b"
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
    models = "/zfs/models";
    openFirewall = true;
  };
}
