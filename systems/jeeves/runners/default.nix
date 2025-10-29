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
    nix-builder-00.enable = true;
    nix-builder-01.enable = true;
    nix-builder-02.enable = true;
    nix-builder-03.enable = true;
    nix-builder-04.enable = true;
    nix-builder-05.enable = true;
    nix-builder-06.enable = true;
    nix-builder-07.enable = true;
    nix-builder-08.enable = true;
    nix-builder-09.enable = true;
    nix-builder-10.enable = true;
    nix-builder-11.enable = true;
    nix-builder-12.enable = true;
    nix-builder-13.enable = true;
    nix-builder-14.enable = true;
  };
}
