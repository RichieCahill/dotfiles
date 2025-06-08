{
  nix.settings = {
    trusted-substituters = [ "http://cache.tmmworkshop.com" ];
    substituters = [ "http://cache.tmmworkshop.com/?priority=1&want-mass-query=true" ];
    trusted-public-keys = [ "cache.tmmworkshop.com:jHffkpgbmEdstQPoihJPYW9TQe6jnQbWR2LqkNGV3iA=" ];
  };
}
