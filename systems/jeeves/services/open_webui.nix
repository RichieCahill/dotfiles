let
  vars = import ../vars.nix;
in
{
  services.open-webui = {
    stateDir = "${vars.services}/open_webui/";
    enable = true;
    openFirewall = true;
  };
}
