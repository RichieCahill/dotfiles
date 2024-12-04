{
  services.zerotierone = {
    enable = true;
    joinNetworks = [ "e4da7455b2ae64ca" ];
  };
  nix.settings = {
    trusted-substituters = [ "http://192.168.90.40:5000" ];
    substituters = [ "http://192.168.90.40:5000/?priority=1&want-mass-query=true" ];
    trusted-public-keys = [ "cache.tmmworkshop.com:jHffkpgbmEdstQPoihJPYW9TQe6jnQbWR2LqkNGV3iA=" ];
  };
}
