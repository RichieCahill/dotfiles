{
  services.n8n = {
    enable = true;

    settings = {
      N8N_HOST = "127.0.0.1";
      N8N_PORT = "5678";
      N8N_PROTOCOL = "https";

      WEBHOOK_URL = "https://n8n.tmmworkshop.com/";
      N8N_EDITOR_BASE_URL = "https://n8n.tmmworkshop.com/";

      DB_TYPE = "postgresdb";
      DB_POSTGRESDB_HOST = "/run/postgresql";
      DB_POSTGRESDB_DATABASE = "n8n";
      DB_POSTGRESDB_USER = "richie";

      N8N_ENCRYPTION_KEY = "generate-a-long-random-key";
      N8N_SECURE_COOKIE = "true";
      N8N_USER_MANAGEMENT_DISABLED = "false";
      N8N_DEFAULT_LOCALE = "en";
      GENERIC_TIMEZONE = "America/New_York";

      N8N_DIAGNOSTICS_ENABLED = "false";
      N8N_VERSION_NOTIFICATIONS_ENABLED = "false";
    };

    # Optional: hardening toggles you might like
    # serviceConfig = {
    #   ProtectHome = "read-only";
    #   ProtectKernelTunables = true;
    #   ProtectKernelModules = true;
    #   PrivateTmp = true;
    #   NoNewPrivileges = true;
    # };
  };
}
