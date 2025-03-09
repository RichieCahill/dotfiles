let
  vars = import ../vars.nix;
in
{
  services = {
    home-assistant = {
      enable = true;
      openFirewall = true;
      configDir = vars.media_home_assistant;
      config = {
        http = {
          server_port = 8123;
          server_host = [
            "192.168.95.14"
            "192.168.90.40"
            "127.0.0.1"
          ];
          use_x_forwarded_for = true;
          trusted_proxies = "127.0.0.1";
        };
        homeassistant = {
          time_zone = "America/New_York";
          unit_system = "us_customary";
          temperature_unit = "F";
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
          aioesphomeapi
          aiounifi
          bleak-esphome
          esphome-dashboard-api
          gtts
          jellyfin-apiclient-python
          psycopg2
          pymetno
          pyownet
          rokuecp
          uiprotect
          wakeonlan
          wyoming
        ];
      extraComponents = [ "isal" ];
    };
    esphome = {
      enable = true;
      openFirewall = true;
      address = "192.168.90.40";
    };
    wyoming = {
      faster-whisper.servers.main = {
        enable = true;
        uri = "tcp://0.0.0.0:10300";
        model = "medium.en";
        language = "en";
        device = "cuda";
      };
      piper.servers.main = {
        enable = true;
        uri = "tcp://0.0.0.0:10200";  
        voice = "en_GB-alba-medium";
      };
    };
  };
}
