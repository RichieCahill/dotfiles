{
  nix.settings = {
    trusted-substituters = [ "http://192.168.95.35:5000" ];
    substituters = [ "http://192.168.95.35:5000/?priority=1&want-mass-query=true" ];
  };
}
