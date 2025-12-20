let
  vars = import ../vars.nix;
in
{
  networking.firewall.allowedTCPPorts = [ 6443 ];

  services.gitea = {
    enable = true;
    appName = "TMM Workshop";
    stateDir = "${vars.services}/gitea/";
    lfs.enable = true;
    recommendedDefaults = true;
    database = {
      type = "postgres";
      name = "gitea";
      user = "gitea";
      socket = "/run/postgresql";
      port = 5432;
      createDatabase = false;
    };
    settings = {
      service.DISABLE_REGISTRATION = true;
      server = {
        DOMAIN = "nayeonie.com";
        ROOT_URL = "https://nayeonie.com/";
        HTTP_PORT = 6443;
        SSH_PORT = 2222;
        SSH_LISTEN_PORT = 2223;
        START_SSH_SERVER = true;
        PUBLIC_URL_DETECTION = "auto";
      };
      repository = {
        ENABLE_PUSH_CREATE_USER = true;
        DEFAULT_MERGE_STYLE = "rebase-merge";
      };
      log = {
        LEVEL = "Trace";
        ENABLE_SSH_LOG = true;
      };
      log.console-warn = {
        LEVEL = "Trace";
        ENABLE_SSH_LOG = true;
      };
    };
  };

  systemd.services.gitea = {
    requires = [ "docker.service" ];
    after = [ "docker.service" ];
  };
}
