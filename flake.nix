{
  description = "My NixOS/home-manager configuration.";

  nixConfig = {
    extra-substituters = [
      "https://cache.nixos.org/?priority=2&want-mass-query=true"
      "https://nix-community.cachix.org/?priority=10&want-mass-query=true"
    ];
    extra-trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=" # cspell:disable-line
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs=" # cspell:disable-line
      "cache-nix-dot:Od9KN34LXc6Lu7y1ozzV1kIXZa8coClozgth/SYE7dU=" # cspell:disable-line
    ];
  };

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    nixpkgs-stable.url = "github:nixos/nixpkgs/nixos-24.05";
    nixpkgs-master.url = "github:nixos/nixpkgs/master";
    systems.url = "github:nix-systems/default-linux";

    nixos-hardware.url = "github:nixos/nixos-hardware/master";

    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    firefox-addons = {
      url = "gitlab:rycee/nur-expressions?dir=pkgs/firefox-addons";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    system_tools = {
      url = "github:RichieCahill/system_tools";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      home-manager,
      systems,
      sops-nix,
      ...
    }@inputs:
    let
      inherit (self) outputs;
      lib = nixpkgs.lib // home-manager.lib;
      forEachSystem = f: lib.genAttrs (import systems) (system: f pkgsFor.${system});
      pkgsFor = lib.genAttrs (import systems) (
        system:
        import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        }
      );
    in
    {
      inherit lib;
      overlays = import ./overlays { inherit inputs outputs; };

      devShells = forEachSystem (pkgs: import ./shell.nix { inherit pkgs; });
      formatter = forEachSystem (pkgs: pkgs.treefmt);

      nixosConfigurations = {
        bob = lib.nixosSystem {
          modules = [
            ./systems/bob
          ];
          specialArgs = { inherit inputs outputs; };
        };
        jeeves = lib.nixosSystem {
          modules = [
            ./systems/jeeves
          ];
          specialArgs = { inherit inputs outputs; };
        };
        rhapsody-in-green = lib.nixosSystem {
          modules = [
            ./systems/rhapsody-in-green
          ];
          specialArgs = { inherit inputs outputs; };
        };
      };
    };
}
