let
  vars = import ./vars.nix;
in
{
  users = {
    users.github-runners = {
      isSystemUser = true;
      group = "github-runners";
      uid = 601;
    };
    groups.github-runners = {
      gid = 601;
    };
  };
  
  services.github-runners.nix_builder = {
    enable = true;
    workDir = "/home/richie/test";
    url = "https://github.com/RichieCahill/dotfiles";
    extraLabels = [ "nixos" ];
    tokenFile = "${vars.storage_secrets}/services/github_runners/nix_builder";
    user = "github-runners";
    group = "github-runners";
    # extraPackages
    # extraEnvironment
  };
}
