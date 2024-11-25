let
  vars = import ./vars.nix;
in
{
  services.github-runners.nix_builder = {
    enable = true;
    workDir = "/home/richie/test";
    url = "https://github.com/RichieCahill/dotfiles";
    extraLabels = [ "nixos" ];
    tokenFile = "${vars.storage_secrets}/services/github_runners/nix_builder";
    # extraPackages
    # extraEnvironment
  };
}
