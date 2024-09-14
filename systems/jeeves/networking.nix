{
  networking = {
    hostName = "jeeves";
    hostId = "0e15ce35";
    firewall.enable = false;
  };

  systemd.network = {
    enable = true;
    networks = {
      "10-1GB_Primary" = {
        matchConfig.Name = "enp98s0f0";
        DHCP = "yes";
      };
    };
    networks = {
      "10-1GB_Secondary" = {
        matchConfig.Name = "enp98s0f1";
        DHCP = "yes";
      };
    };
    networks = {
      "10-10GB_Primary" = {
        matchConfig.Name = "enp97s0f0np0";
        DHCP = "yes";
        linkConfig.RequiredForOnline = "routable";
      };
    };
    networks = {
      "10-10GB_Secondary" = {
        matchConfig.Name = "enp97s0f1np1";
        DHCP = "yes";
      };
    };
  };

  services.zerotierone = {
    enable = true;
    joinNetworks = [ "e4da7455b2ae64ca" ];
  };
}
