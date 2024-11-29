{
  networking = {
    hostName = "jeeves";
    hostId = "0e15ce35";
    firewall.enable = true;
    useNetworkd = true;
  };

  systemd.network = {

    enable = true;

    netdevs = {
      "20-ioit-vlan" = {
        netdevConfig = {
          Kind = "vlan";
          Name = "ioit-vlan";
        };
        vlanConfig.Id = 20;
      };
    };

    networks = {
      "10-1GB_Primary" = {
        matchConfig.Name = "enp98s0f0";
        address = [ "192.168.95.14/24" ];
        routes = [{ Gateway = "192.168.95.1"; }];
        vlan = [ "ioit-vlan" ];
        linkConfig.RequiredForOnline = "routable";
      };
      "10-1GB_Secondary" = {
        matchConfig.Name = "enp98s0f1";
        DHCP = "yes";
      };
      "10-10GB_Primary" = {
        matchConfig.Name = "enp97s0f0np0";
        DHCP = "yes";
        linkConfig.RequiredForOnline = "routable";
      };
      "10-10GB_Secondary" = {
        matchConfig.Name = "enp97s0f1np1";
        DHCP = "yes";
      };
      "40-ioit-vlan" = {
        matchConfig.Name = "ioit-vlan";
        DHCP = "yes";
      };
    };
  };

  services.zerotierone = {
    enable = true;
    joinNetworks = [ "e4da7455b2ae64ca" ];
  };
}
