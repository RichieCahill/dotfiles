{
  services.syncthing = {
    enable = true;
    user = "richie";
    overrideDevices = true;
    overrideFolders = true;
    dataDir = "/home/richie/Syncthing";
    configDir = "/home/richie/.config/syncthing";
    settings = {
      devices = {
        phone.id = "LTGPLAE-M4ZDJTM-TZ3DJGY-SLLAVWF-CQDVEVS-RGCS75T-GAPZYK3-KUM6LA5"; # cspell:disable-line
        jeeves.id = "RCDU465-AIQRBEJ-VWC4EZF-2AMXABC-F3S4NFW-QA4ZUAQ-OVNUBLI-BUJJTA2"; # cspell:disable-line
        ipad.id = "KI76T3X-SFUGV2L-VSNYTKR-TSIUV5L-SHWD3HE-GQRGRCN-GY4UFMD-CW6Z6AX"; # cspell:disable-line
        bob.id = "CJIAPEJ-VO74RR4-F75VU6M-QNZAMYG-FYUJG7Y-6AT62HJ-355PRPL-PJFETAZ"; # cspell:disable-line
        rhapsody-in-green.id = "ASL3KC4-3XEN6PA-7BQBRKE-A7JXLI6-DJT43BY-Q4WPOER-7UALUAZ-VTPQ6Q4"; # cspell:disable-line
      };
    };
  };
}
