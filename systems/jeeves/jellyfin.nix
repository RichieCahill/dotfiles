let
  vars = import ./vars.nix;
in
{
  services.jellyfin = {
    enable = true;
    openFirewall = true;
    dataDir = "${vars.media_services}/jellyfin";
  };
}
