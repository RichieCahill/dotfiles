{
  programs.git = {
    enable = true;
    userEmail = "Richie@tmmworkshop.com";
    userName = "Richie Cahill";
    settings = {
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
