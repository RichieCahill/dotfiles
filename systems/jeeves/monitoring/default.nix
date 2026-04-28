{
  lib,
  pkgs,
  ...
}:
let
  vars = import ../vars.nix;


  prometheusDataRoot = "${vars.database}/prometheus";
  mainPrometheusDataDir = "${prometheusDataRoot}/main";
  pidPrometheusDataDir = "${prometheusDataRoot}/pid-short";

  prometheusYaml = pkgs.formats.yaml { };

  mkPrometheusConfig =
    name: cfg:
    let
      configFile = prometheusYaml.generate "${name}.yaml" cfg;
    in
    pkgs.runCommand "${name}-checked.yaml"
      {
        nativeBuildInputs = [ pkgs.prometheus.cli ];
      }
      ''
        promtool check config ${configFile}
        cp ${configFile} $out
      '';

  mkTarget = host: address: {
    targets = [ address ];
    labels.instance = host;
  };

  mainPrometheusConfig = mkPrometheusConfig "prometheus-main" {
    global = {
      scrape_interval = "30s";
      scrape_timeout = "10s";
      evaluation_interval = "30s";
    };
    scrape_configs = [
      {
        job_name = "node";
        static_configs = [
          (mkTarget "jeeves" "192.168.90.40:9100")
          (mkTarget "bob" "192.168.90.25:9100")
        ];
      }
      {
        job_name = "process_grouped";
        static_configs = [
          (mkTarget "jeeves" "192.168.90.40:9256")
          (mkTarget "bob" "192.168.90.25:9256")
        ];
      }
      {
        job_name = "smartctl";
        static_configs = [
          (mkTarget "jeeves" "192.168.90.40:9633")
          (mkTarget "bob" "192.168.90.25:9633")
        ];
      }
      {
        job_name = "zfs";
        static_configs = [
          (mkTarget "jeeves" "192.168.90.40:9134")
          (mkTarget "bob" "192.168.90.25:9134")
        ];
      }
    ];
  };

  pidPrometheusConfig = mkPrometheusConfig "prometheus-pid-short" {
    global = {
      scrape_interval = "15s";
      scrape_timeout = "10s";
      evaluation_interval = "15s";
    };
    scrape_configs = [
      {
        job_name = "process_pid";
        static_configs = [
          (mkTarget "jeeves" "192.168.90.40:9257")
          (mkTarget "bob" "192.168.90.25:9257")
        ];
      }
    ];
  };

  mkPrometheusService =
    {
      dataDir,
      configFile,
      port,
      retention,
    }:
    {
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        ExecStart = "${lib.getExe pkgs.prometheus} ${
          lib.escapeShellArgs [
            "--config.file=${configFile}"
            "--storage.tsdb.path=${dataDir}"
            "--storage.tsdb.retention.time=${retention}"
            "--web.listen-address=127.0.0.1:${toString port}"
          ]
        }";
        User = "prometheus";
        Group = "prometheus";
        Restart = "always";
        RestartSec = "5s";
        WorkingDirectory = dataDir;
        ReadWritePaths = [ dataDir ];
        CapabilityBoundingSet = [ "" ];
        DeviceAllow = [ "/dev/null rw" ];
        DevicePolicy = "strict";
        LockPersonality = true;
        MemoryDenyWriteExecute = true;
        NoNewPrivileges = true;
        PrivateDevices = true;
        PrivateTmp = true;
        ProtectClock = true;
        ProtectControlGroups = true;
        ProtectHome = true;
        ProtectHostname = true;
        ProtectKernelLogs = true;
        ProtectKernelModules = true;
        ProtectKernelTunables = true;
        ProtectProc = "invisible";
        ProtectSystem = "strict";
        RemoveIPC = true;
        RestrictAddressFamilies = [
          "AF_INET"
          "AF_INET6"
          "AF_UNIX"
        ];
        RestrictNamespaces = true;
        RestrictRealtime = true;
        RestrictSUIDSGID = true;
        SystemCallArchitectures = "native";
        SystemCallFilter = [
          "@system-service"
          "~@privileged"
        ];
      };
    };
in
{
  users = {
    groups.prometheus = { };
    users.prometheus = {
      isSystemUser = true;
      group = "prometheus";
      description = "Prometheus daemon user";
    };
  };

  systemd = {
    services = {
      prometheus-main = mkPrometheusService {
        configFile = mainPrometheusConfig;
        dataDir = mainPrometheusDataDir;
        port = 9090;
        retention = "90d";
      };

      prometheus-pid-short = mkPrometheusService {
        configFile = pidPrometheusConfig;
        dataDir = pidPrometheusDataDir;
        port = 9092;
        retention = "10m";
      };
    };

    tmpfiles.rules = [
      "d ${prometheusDataRoot} 0755 root root - -"
      "d ${mainPrometheusDataDir} 0750 prometheus prometheus - -"
      "d ${pidPrometheusDataDir} 0750 prometheus prometheus - -"
    ];
  };
}
