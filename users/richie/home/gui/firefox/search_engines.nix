{ pkgs, ... }:
{
  programs.firefox.profiles.richie.search.engines = {
    "Nix Options" = {
      urls = [
        {
          template = "https://search.nixos.org/options";
          params = [
            {
              name = "type";
              value = "packages";
            }
            {
              name = "channel";
              value = "unstable";
            }
            {
              name = "query";
              value = "{searchTerms}";
            }
          ];
        }
      ];
      icon = "${pkgs.nixos-icons}/share/icons/hicolor/scalable/apps/nix-snowflake.svg";
      definedAliases = [ "@o" ];
    };
    "Nix Packages" = {
      urls = [
        {
          template = "https://search.nixos.org/packages";
          params = [
            {
              name = "type";
              value = "packages";
            }
            {
              name = "channel";
              value = "unstable";
            }
            {
              name = "query";
              value = "{searchTerms}";
            }
          ];
        }
      ];
      icon = "${pkgs.nixos-icons}/share/icons/hicolor/scalable/apps/nix-snowflake.svg";
      definedAliases = [ "@n" ];
    };
    "Nix Packages pr-tracker" = {
      urls = [
        {
          template = "https://nixpk.gs/pr-tracker.html?";
          params = [
            {
              name = "pr";
              value = "{searchTerms}";
            }
          ];
        }
      ];
      icon = "${pkgs.nixos-icons}/share/icons/hicolor/scalable/apps/nix-snowflake.svg";
      definedAliases = [ "@nprt" ];
    };
    "kagi" = {
      urls = [
        {
          template = "https://kagi.com/search?";
          params = [
            {
              name = "q";
              value = "{searchTerms}";
            }
          ];
        }
      ];
      icon = ./kagi.png;
    };
    github = {
      urls = [
        {
          template = "https://github.com/search?";
          params = [
            {
              name = "q";
              value = "{searchTerms}";
            }
            {
              name = "type";
              value = "code";
            }
          ];
        }
      ];
      icon = ./github.svg;
      definedAliases = [ "@g" ];
    };
  };
}
