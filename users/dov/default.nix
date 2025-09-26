{
  pkgs,
  ...
}:
{

  users = {
    users.dov = {
      isNormalUser = true;

      shell = pkgs.zsh;
      group = "dov";
      openssh.authorizedKeys.keys = [
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCoSBmMfvp6aThkrfkLQ4TDwZJD0HCC0lsTIRNREIAWeduNkVFdkO3T1SMLmCKJ+zlL9xziNBEqB8NFl4TabAhptIGlKgTOc8C9eDaPQMQV8PB/4DxZhCt7O2qb4Vfcz82IHPtdwwaIsGpssgh81mQ4tPtP8BI0TluRBy+2v095s20j+PYRGrAXJtOWpVY9zaXxEJ8dXDhHDF2xzxvUcwu9NsoY8t+4/ZJ1mrTTG+eGp5gLAKnSVhAGgsmqCY577Nkso1jSzKer1XcCiaGIedpLuTzmUbOFFEVhhTSy+Ki1NLEcjGW2e6Vyg5Pm8VGN75MqyDZsi5igv9Grxq62EHQ4mFea9rns48B74O/bNQ1OoLVO9u/HwdLCgBTZzptrCmNwML6kBWrmCogoH3ueVbHwDCW5kTTMBCoVV+HaZ+qDWu7xZVx49MuCK29QGZj/IrN0N7h78KL0NYajdei87R0mcmWGP0YaJTdCQ4iKi9c77BUYQp+Qpqt+mnIX0cgjQOU= dkruger@kzin" # cspell:disable-line
      ];
      extraGroups = [
        "audio"
        "video"
        "users"
      ];
      uid = 1004;
    };

    groups.dov.gid = 1004;
  };
}
