{ lib, ... }:
{
  services.syncthing = {
    enable = true;
    user = "richie";
    overrideDevices = true;
    overrideFolders = lib.mkDefault true;
    dataDir = "/home/richie/Syncthing";
    configDir = "/home/richie/.config/syncthing";
    settings.devices = {
      bob.id = "CJIAPEJ-VO74RR4-F75VU6M-QNZAMYG-FYUJG7Y-6AT62HJ-355PRPL-PJFETAZ"; # cspell:disable-line
      brain.id = "SSCGIPI-IV3VYKB-TRNIJE3-COV4T2H-CDBER7F-I2CGHYA-NWOEUDU-3T5QAAN"; # cspell:disable-line
      ipad.id = "KI76T3X-SFUGV2L-VSNYTKR-TSIUV5L-SHWD3HE-GQRGRCN-GY4UFMD-CW6Z6AX"; # cspell:disable-line
      jeeves.id = "ICRHXZW-ECYJCUZ-I4CZ64R-3XRK7CG-LL2HAAK-FGOHD22-BQA4AI6-5OAL6AG"; # cspell:disable-line
      phone.id = "TBRULKD-7DZPGGZ-F6LLB7J-MSO54AY-7KLPBIN-QOFK6PX-W2HBEWI-PHM2CQI"; # cspell:disable-line
      rhapsody-in-green.id = "ASL3KC4-3XEN6PA-7BQBRKE-A7JXLI6-DJT43BY-Q4WPOER-7UALUAZ-VTPQ6Q4"; # cspell:disable-line
    };
  };
}
