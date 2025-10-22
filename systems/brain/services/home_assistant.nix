{
  users = {
    users.hass = {
      isSystemUser = true;
      group = "hass";
    };
    groups.hass = { };
  };

  services = {
    home-assistant = {
      enable = true;
      openFirewall = true;
      config = {
        http = {
          server_port = 8123;
          server_host = [
            "192.168.90.35"
            "192.168.95.35"
            "127.0.0.1"
          ];
          use_x_forwarded_for = true;
          trusted_proxies = "192.168.90.40";
        };
        homeassistant = {
          time_zone = "America/New_York";
          unit_system = "us_customary";
          temperature_unit = "F";
          packages = {
            victron_modbuss = "!include ${home_assistant/victron_modbuss.yaml}";
          };
        };
        recorder = {
          db_url = "postgresql://@/hass";
          auto_purge = true;
          purge_keep_days = 3650;
          db_retry_wait = 15;
        };
        assist_pipeline = { };
        backup = { };
        bluetooth = { };
        config = { };
        dhcp = { };
        energy = { };
        history = { };
        homeassistant_alerts = { };
        image_upload = { };
        logbook = { };
        media_source = { };
        mobile_app = { };
        ssdp = { };
        sun = { };
        webhook = { };
        zeroconf = { };
        automation = "!include automations.yaml";
        script = "!include scripts.yaml";
        scene = "!include scenes.yaml";
        group = "!include groups.yaml";
      };
      extraPackages =
        python3Packages: with python3Packages; [
          pymodbus # for modbus
          gtts # not sure what wants this
          jellyfin-apiclient-python # for jellyfin
          paho-mqtt # for mqtt
          psycopg2 # for postgresql
          forecast-solar # for solar forecast
        ];
      extraComponents = [ "isal" ];
    };
    esphome = {
      enable = true;
      openFirewall = true;
      address = "192.168.90.35";
    };
  };
}
