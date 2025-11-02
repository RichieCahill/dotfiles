{
  programs.ssh = {
    enable = true;
    enableDefaultConfig = false;
    matchBlocks = {
      jeeves = {
        hostname = "192.168.90.40";
        user = "richie";
        identityFile = "~/.ssh/id_ed25519";
        port = 629;
        dynamicForwards = [ { port = 9050; } ];
        compression = true;
      };
      unlock-jeeves = {
        hostname = "192.168.99.14";
        user = "root";
        identityFile = "~/.ssh/id_ed25519";
        port = 2222;
      };
      brain = {
        hostname = "192.168.90.35";
        user = "richie";
        identityFile = "~/.ssh/id_ed25519";
        port = 129;
        dynamicForwards = [ { port = 9050; } ];
      };
      unlock-brain = {
        hostname = "192.168.95.35";
        user = "root";
        identityFile = "~/.ssh/id_ed25519";
        port = 2222;
      };
      bob = {
        hostname = "192.168.90.25";
        user = "richie";
        identityFile = "~/.ssh/id_ed25519";
        port = 262;
        dynamicForwards = [ { port = 9050; } ];
      };
      rhapsody-in-green = {
        hostname = "192.168.90.221";
        user = "richie";
        identityFile = "~/.ssh/id_ed25519";
        port = 922;
      };
      leviathan = {
        hostname = "192.168.90.127";
        user = "richie";
        identityFile = "~/.ssh/id_ed25519";
        port = 332;
      };
    };
  };
}
