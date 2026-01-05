{
  pkgs ? import <nixpkgs> { },
  ...
}:
{
  default = pkgs.mkShell {
    NIX_CONFIG = "extra-experimental-features = nix-command flakes ca-derivations";
    nativeBuildInputs = with pkgs; [
      age
      busybox
      git
      gnupg
      home-manager
      my_python
      nix
      ssh-to-age
    ];
  };
}
