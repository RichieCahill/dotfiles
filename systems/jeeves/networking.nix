{
  networking = {
    hostName = "jeeves";
    hostId = "0e15ce35";
    firewall = {
      enable = true;
      interfaces.br-nix-builder = {
        allowedTCPPorts = [ ];
        allowedUDPPorts = [ ];
      };
    };
    useNetworkd = true;
  };

  systemd.network = {
    enable = true;
    wait-online = {
      enable = false;
      anyInterface = true;
    };
    netdevs = {
      "20-br-nix-builder" = {
        netdevConfig = {
          Kind = "bridge";
          Name = "br-nix-builder";
        };
      };
      "30-internet-vlan" = {
        netdevConfig = {
          Kind = "vlan";
          Name = "internet-vlan";
        };
        vlanConfig.Id = 100;
      };
    };
    networks = {
      "10-1GB_Primary" = {
        matchConfig.Name = "enp97s0f1";
        address = [ "192.168.99.14/24" ];
        routes = [ { Gateway = "192.168.99.1"; } ];
        vlan = [ "internet-vlan" ];
        linkConfig.RequiredForOnline = "routable";
      };
      "50-internet-vlan" = {
        matchConfig.Name = "internet-vlan";
        bridge = [ "br-nix-builder" ];
        linkConfig.RequiredForOnline = "no";
      };
      "60-br-nix-builder" = {
        matchConfig.Name = "br-nix-builder";
        bridgeConfig = { };
        address = [ "192.168.3.10/24" ];
        routingPolicyRules = [
          {
            From = "192.168.3.0/24";
            Table = 100;
            Priority = 100;
          }
        ];
        routes = [
          {
            Gateway = "192.168.3.1";
            Table = 100;
            GatewayOnLink = false;
            Metric = 2048;
            PreferredSource = "192.168.3.10";
          }
        ];
        linkConfig.RequiredForOnline = "no";
      };
    };
  };
}
