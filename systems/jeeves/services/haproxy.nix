{
  networking.firewall.allowedTCPPorts = [ 80 443 ];

  services.haproxy = {
    enable = true;
    config = builtins.readFile ./haproxy.cfg;
  };
}