{
  ...
}:
let
  vars = import ../vars.nix;
  grafanaDataDir = "${vars.services}/grafana";
in
{
  networking.firewall.allowedTCPPorts = [ 3000 ];

  services.grafana = {
    enable = true;
    dataDir = grafanaDataDir;
    settings = {
      database.type = "sqlite3";
      security = {
        admin_password = "$__file{${vars.secrets}/services/grafana/admin_password}";
        admin_user = "admin";
        secret_key = "$__file{${vars.secrets}/services/grafana/secret_key}";
      };
      server = {
        http_addr = "192.168.90.40";
        http_port = 3000;
        root_url = "http://192.168.90.40:3000/";
      };
    };
    provision = {
      enable = true;
      dashboards.settings = {
        apiVersion = 1;
        providers = [
          {
            name = "monitoring";
            folder = "Monitoring";
            type = "file";
            disableDeletion = false;
            editable = false;
            allowUiUpdates = false;
            updateIntervalSeconds = 30;
            options.path = ../monitoring/dashboards;
          }
        ];
      };
      datasources.settings = {
        apiVersion = 1;
        prune = true;
        datasources = [
          {
            access = "proxy";
            editable = false;
            isDefault = true;
            name = "prom-main";
            type = "prometheus";
            uid = "prom-main";
            url = "http://127.0.0.1:9090";
          }
          {
            access = "proxy";
            editable = false;
            name = "prom-pid-short";
            type = "prometheus";
            uid = "prom-pid-short";
            url = "http://127.0.0.1:9092";
          }
        ];
      };
    };
  };

  systemd = {
    services.grafana.after = [
      "prometheus-main.service"
      "prometheus-pid-short.service"
    ];

    tmpfiles.rules = [
      "d ${grafanaDataDir} 0750 grafana grafana - -"
    ];
  };
}
