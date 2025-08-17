{
  services = {
    ollama = {
      user = "ollama";
      enable = true;
      hosts = "0.0.0.0";
      loadModels = [
        "qwen3:14b"
        "qwen3:30b"
        "gemma3:12b"
        "gemma3:27b"
        "gpt-oss:20b"
        "gpt-oss:120b"
        "codellama:7b"
        "deepseek-r1:8b"
        "deepseek-r1:14b"
        "deepseek-r1:32b"
      ];
      models = "/zfs/storage/models";
      openFirewall = true;
    };
  };
}
