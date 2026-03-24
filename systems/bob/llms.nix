{
  services.ollama = {
    user = "ollama";
    host = "0.0.0.0";
    enable = true;

    syncModels = true;
    loadModels = [
      "codellama:7b"
      "deepscaler:1.5b"
      "deepseek-r1:14b"
      "deepseek-r1:32b"
      "deepseek-r1:8b"
      "devstral-small-2:24b"
      "dolphin-llama3:8b"
      "functiongemma:270m"
      "gemma3:12b"
      "gemma3:27b"
      "glm-4.7-flash:q4_K_M"
      "gpt-oss:20b"
      "huihui_ai/dolphin3-abliterated:8b"
      "lfm2:24b"
      "magistral:24b"
      "ministral-3:14b"
      "nemotron-3-nano:30b"
      "nemotron-cascade-2:30b"
      "qwen3-coder:30b"
      "qwen3-embedding:0.6b"
      "qwen3-embedding:4b"
      "qwen3-embedding:8b"
      "qwen3-vl:2b"
      "qwen3-vl:32b"
      "qwen3-vl:4b"
      "qwen3-vl:8b"
      "qwen3:0.6b"
      "qwen3:1.7b"
      "qwen3:14b"
      "qwen3:30b"
      "qwen3:32b"
      "qwen3:4b"
      "qwen3:8b"
      "qwen3.5:27b"
      "qwen3.5:35b"
      "translategemma:12b"
      "translategemma:27b"
      "translategemma:4b"
    ];
    models = "/zfs/models";
    openFirewall = true;
  };
}
