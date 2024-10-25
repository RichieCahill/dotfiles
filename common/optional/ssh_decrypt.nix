{ config, ... }:
{
  boot.initrd = {
    network = {
      enable = true;
      ssh = {
        enable = true;
        port = 2222;
        hostKeys = [ "/etc/ssh/initrd_ssh_host_ed25519_key" ];
        authorizedKeys = config.users.users.richie.openssh.authorizedKeys.keys;
      };
    };
    availableKernelModules = [ "igb" ];
  };
}
