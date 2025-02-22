{
  services = {
    ollama = {
      user = "ollama";
      enable = true;
      loadModels = [
        "codellama:7b"
        "deepseek-r1:8b"
        "deepseek-r1:14b"
        "deepseek-r1:32b"
        "llama3.2:3b"
        "llama2-uncensored:7b"
        "mistral-nemo:12b"
        "dolphin-mixtral:8x7b"
      ];
      models = "/zfs/models";
      acceleration = "cuda";
      openFirewall = true;
    };
    open-webui = {
      enable = true;
      openFirewall = true;
      host = "192.168.90.25";
    };
  };
}
