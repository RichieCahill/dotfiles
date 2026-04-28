{
  config,
  lib,
  pkgs,
  ...
}:
let
  monitoringInterface = "ztwfunumly";
  nodeTextfileDir = "/var/lib/prometheus-node-exporter-textfile";

  mkProcessNameTemplate =
    perPid: template: if perPid then "${template}:{{.PID}}:{{.StartTime}}" else template;

  mkProcessMatchers = perPid: [
    {
      name = mkProcessNameTemplate perPid "{{.Username}}:{{.Matches.Module}}";
      cmdline = [ "^/nix/store[^ ]*/bin/python[^ ]* -m (?P<Module>[^ ]+)" ];
    }
    {
      name = mkProcessNameTemplate perPid "{{.Username}}:{{.Matches.Wrapped}}";
      cmdline = [
        "^/nix/store[^ ]*/bin/python[^ ]* /nix/store[^ ]*/bin/\\.?(?P<Wrapped>[^ /]+?)(?:-wrapped)?(?:\\s|$)"
      ];
    }
    {
      name = mkProcessNameTemplate perPid "{{.Username}}:{{.Matches.Wrapped}}";
      cmdline = [
        "^/nix/store[^ ]*/bin/node /nix/store[^ ]*-(?P<Wrapped>[A-Za-z0-9._+-]+)-[0-9][^ /]*/"
      ];
    }
    {
      name = mkProcessNameTemplate perPid "{{.Username}}:{{.Matches.Wrapped}}";
      cmdline = [ "^/nix/store[^ ]*/(?:bin/|lib/[^ ]*/)?\\.?(?P<Wrapped>[^ /]+?)(?:-wrapped)?(?:\\s|$)" ];
    }
    {
      name = mkProcessNameTemplate perPid "{{.Username}}:{{.ExeBase}}";
      cmdline = [ ".+" ];
    }
  ];

  perPidConfig = pkgs.writeText "process-exporter-per-pid.yaml" (
    builtins.toJSON {
      process_names = mkProcessMatchers true;
    }
  );

  zpoolLatencyScript = pkgs.writeShellScript "zpool-latency-exporter" ''
        set -euo pipefail

        out_dir=${lib.escapeShellArg nodeTextfileDir}
        host=${lib.escapeShellArg config.networking.hostName}
        tmp_file="$(mktemp "$out_dir/zpool.prom.XXXXXX")"
        trap 'rm -f "$tmp_file"' EXIT

        pools="$(zpool list -H -o name | paste -sd, -)"

        cat >"$tmp_file" <<'EOF'
    # HELP zpool_iostat_total_wait_read_ns Average total read wait time reported by zpool iostat.
    # TYPE zpool_iostat_total_wait_read_ns gauge
    # HELP zpool_iostat_total_wait_write_ns Average total write wait time reported by zpool iostat.
    # TYPE zpool_iostat_total_wait_write_ns gauge
    # HELP zpool_iostat_disk_wait_read_ns Average disk read wait time reported by zpool iostat.
    # TYPE zpool_iostat_disk_wait_read_ns gauge
    # HELP zpool_iostat_disk_wait_write_ns Average disk write wait time reported by zpool iostat.
    # TYPE zpool_iostat_disk_wait_write_ns gauge
    # HELP zpool_iostat_syncq_wait_read_ns Average synchronous queue read wait time reported by zpool iostat.
    # TYPE zpool_iostat_syncq_wait_read_ns gauge
    # HELP zpool_iostat_syncq_wait_write_ns Average synchronous queue write wait time reported by zpool iostat.
    # TYPE zpool_iostat_syncq_wait_write_ns gauge
    # HELP zpool_iostat_asyncq_wait_read_ns Average asynchronous queue read wait time reported by zpool iostat.
    # TYPE zpool_iostat_asyncq_wait_read_ns gauge
    # HELP zpool_iostat_asyncq_wait_write_ns Average asynchronous queue write wait time reported by zpool iostat.
    # TYPE zpool_iostat_asyncq_wait_write_ns gauge
    EOF

        zpool iostat -Hplvy -y 1 1 | awk -F '\t' -v host="$host" -v pools="$pools" '
          function esc(str, out) {
            out = str
            gsub(/\\/, "\\\\", out)
            gsub(/"/, "\\\"", out)
            return out
          }

          function emit(metric, pool, vdev, value) {
            if (value == "" || value == "-") {
              return
            }

            printf "%s{host=\"%s\",pool=\"%s\",vdev=\"%s\"} %s\n",
              metric,
              esc(host),
              esc(pool),
              esc(vdev),
              value
          }

          BEGIN {
            split(pools, pool_names, ",")
            for (idx in pool_names) {
              if (pool_names[idx] != "") {
                known_pools[pool_names[idx]] = 1
              }
            }
          }

          NF == 0 {
            next
          }

          {
            row_name = $1

            if (row_name in known_pools) {
              current_pool = row_name
              current_vdev = "_pool"
            } else if (current_pool == "") {
              next
            } else {
              current_vdev = row_name
            }

            emit("zpool_iostat_total_wait_read_ns", current_pool, current_vdev, $8)
            emit("zpool_iostat_total_wait_write_ns", current_pool, current_vdev, $9)
            emit("zpool_iostat_disk_wait_read_ns", current_pool, current_vdev, $10)
            emit("zpool_iostat_disk_wait_write_ns", current_pool, current_vdev, $11)
            emit("zpool_iostat_syncq_wait_read_ns", current_pool, current_vdev, $12)
            emit("zpool_iostat_syncq_wait_write_ns", current_pool, current_vdev, $13)
            emit("zpool_iostat_asyncq_wait_read_ns", current_pool, current_vdev, $14)
            emit("zpool_iostat_asyncq_wait_write_ns", current_pool, current_vdev, $15)
          }
        ' >>"$tmp_file"

        mv "$tmp_file" "$out_dir/zpool.prom"
        trap - EXIT
  '';
in
{
  networking.firewall.interfaces.${monitoringInterface}.allowedTCPPorts = [
    9100
    9134
    9256
    9257
    9633
  ];

  services.prometheus.exporters = {
    node = {
      enable = true;
      enabledCollectors = [
        "pressure"
        "processes"
        "systemd"
      ];
      extraFlags = [ "--collector.textfile.directory=${nodeTextfileDir}" ];
    };

    process = {
      enable = true;
      user = "root";
      group = "root";
      settings.process_names = mkProcessMatchers false;
      extraFlags = [
        "-gather-smaps=false"
        "-remove-empty-groups=true"
        "-threads=false"
      ];
    };

    smartctl.enable = true;
    zfs.enable = true;
  };

  programs.atop = {
    enable = true;
    atopService.enable = true;
    atopRotateTimer.enable = true;
    atopacctService.enable = true;
    settings.interval = 30;
  };

  systemd = {
    services = {
      prometheus-process-pid-exporter = {
        description = "Prometheus process exporter with per-PID naming";
        wantedBy = [ "multi-user.target" ];
        after = [ "network.target" ];
        serviceConfig = {
          ExecStart = ''
            ${pkgs.prometheus-process-exporter}/bin/process-exporter \
              --web.listen-address 0.0.0.0:9257 \
              --config.path ${perPidConfig} \
              -children=false \
              -gather-smaps=false \
              -remove-empty-groups=true \
              -threads=false
          '';
          User = "root";
          Group = "root";
          Restart = "always";
          WorkingDirectory = "/tmp";
          CapabilityBoundingSet = [ "" ];
          DeviceAllow = [ "" ];
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
          ProtectSystem = "strict";
          RemoveIPC = true;
          RestrictAddressFamilies = [
            "AF_INET"
            "AF_INET6"
          ];
          RestrictNamespaces = true;
          RestrictRealtime = true;
          RestrictSUIDSGID = true;
          SystemCallArchitectures = "native";
          UMask = "0077";
        };
      };

      zpool-latency-exporter = {
        description = "Exports ZFS latency metrics for node_exporter textfile collection";
        after = [ "zfs-import.target" ];
        requires = [ "zfs-import.target" ];
        path = [
          config.boot.zfs.package
          pkgs.coreutils
          pkgs.gawk
        ];
        serviceConfig = {
          Type = "oneshot";
          ExecStart = zpoolLatencyScript;
        };
      };
    };

    timers.zpool-latency-exporter = {
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnBootSec = "2m";
        OnUnitActiveSec = "60s";
        Unit = "zpool-latency-exporter.service";
      };
    };

    tmpfiles.rules = [ "d ${nodeTextfileDir} 0755 root root - -" ];
  };
}
