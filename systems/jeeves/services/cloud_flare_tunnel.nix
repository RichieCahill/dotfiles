{ pkgs, ... }:
let
  vars = import ../vars.nix;
in
{
  systemd.services.cloud_flare_tunnel = {
    description = "cloud_flare_tunnel proxy's traffic through cloudflare";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      EnvironmentFile = "${vars.secrets}/docker/cloud_flare_tunnel";
      ExecStart = "${pkgs.cloudflared}/bin/cloudflared --no-autoupdate tunnel run";
      Restart = "on-failure";
    };
  };
}
