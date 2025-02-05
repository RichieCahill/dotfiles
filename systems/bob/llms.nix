{
  services = {
    ollama = {
      enable = true;
      loadModels = [ 
        "codellama:7b"
        "deepseek-r1:1.5b"
        "deepseek-r1:7b"
        "deepseek-r1:8b"
        "deepseek-r1:14b"
        "deepseek-r1:32b"
        "llama3.2:3b"
        "mistral-nemo:12b"
      ];
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