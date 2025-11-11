{
  config,
  pkgs,
  ...
}:

let
  vars = import ../vars.nix;
in
{

  # environment.systemPackages = with pkgs; [ php.withExtensions ({ all, ... }: [ all.pdo_pgsql ]) ];

  services.httpd = {
    enable = true;
    adminAddr = "webmaster@localhost";

    enablePHP = true;
    phpPackage = pkgs.php.withExtensions (
      { enabled, all }:
      enabled
      ++ [
        all.pdo
        all.pdo_pgsql
      ]
    );
    extraModules = [ "rewrite" ];
    virtualHosts.great_cloud_of_witnesses = {
      hostName = "localhost";
      listen = [
        {
          ip = "*";
          port = 8092;
        }

      ];
      documentRoot = "${vars.services}/great_cloud_of_witnesses";
      extraConfig = ''
        <Directory "${vars.services}/great_cloud_of_witnesses">
          AllowOverride All
          Require all granted
        </Directory>
      '';
    };
  };

  sops.secrets.gcw_password = {
    sopsFile = ../../../users/secrets.yaml;
    neededForUsers = true;
  };

  users = {
    users.gcw = {
      isSystemUser = true;
      hashedPasswordFile = config.sops.secrets.gcw_password.path;
      group = "gcw";
    };
    groups.gcw = { };
  };
}
