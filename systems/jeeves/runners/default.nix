{ pkgs, ... }:
{
  imports = [ ./nix_builder.nix ];

  users = {
    users.github-runners = {
      shell = pkgs.bash;
      isSystemUser = true;
      group = "github-runners";
      uid = 601;
      openssh.authorizedKeys.keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA/S8i+BNX/12JNKg+5EKGX7Aqimt5KM+ve3wt/SyWuO github-runners" # cspell:disable-line
      ];
    };
    groups.github-runners.gid = 601;
  };
  

  services.nix_builder.containers = {
    nix-builder-0.enable = true;
    nix-builder-1.enable = true;
    nix-builder-2.enable = true;
    nix-builder-3.enable = true;
    nix-builder-4.enable = true;
    nix-builder-5.enable = true;
  };
}
