let
  vars = import ../vars.nix;
in
{
  services.jellyfin = {
    enable = true;
    openFirewall = true;
    dataDir = "${vars.services}/jellyfin";
    cacheDir = "${vars.services}/jellyfin/cache";
  };
}
