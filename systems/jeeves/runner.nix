{
  imports = [
    ./nix_builder.nix
  ];

  users = {
    users.github-runners = {
      isSystemUser = true;
      group = "github-runners";
      uid = 601;
    };
    groups.github-runners.gid = 601;
  };
  

  services.nix_builder.containers = {
    nix-builder-0.enable = true;
    nix-builder-1.enable = true;
    nix-builder-2.enable = true;
  };
}