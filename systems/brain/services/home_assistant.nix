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
        http.server_port = 8123;
        homeassistant = {
          time_zone = "America/New_York";
          unit_system = "us_customary";
          temperature_unit = "F";
          packages = {
            victron_modbuss = "!include ${./home_assistant/victron_modbuss.yaml}";
            battery_sensors = "!include ${./home_assistant/battery_sensors.yaml}";
            gps_location = "!include ${./home_assistant/gps_location.yaml}";
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
        cloud = { };
        zeroconf = { };
        automation = "!include automations.yaml";
        script = "!include scripts.yaml";
        scene = "!include scenes.yaml";
        group = "!include groups.yaml";
      };
      extraPackages =
        python3Packages: with python3Packages; [
          aioesphomeapi # for esphome
          aiounifi # for ubiquiti integration
          bleak-esphome # for esphome
          esphome-dashboard-api # for esphome
          forecast-solar # for solar forecast
          gtts # not sure what wants this
          ical # for todo
          jellyfin-apiclient-python # for jellyfin
          paho-mqtt # for mqtt
          psycopg2 # for postgresql
          py-improv-ble-client # for esphome
          pymodbus # for modbus
          pyopenweathermap # for weather
          pymetno # for met.no weather
          uiprotect # for ubiquiti integration
          unifi-discovery # for ubiquiti integration
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
