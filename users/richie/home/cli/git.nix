{
  programs.git = {
    enable = true;
    signing.format = null;
    settings = {
      user = {
        email = "Richie@tmmworkshop.com";
        name = "Richie Cahill";
      };
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
