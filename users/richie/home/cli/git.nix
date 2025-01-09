{
  programs.git = {
    enable = true;
    userEmail = "Richie@tmmworkshop.com";
    userName = "Richie Cahill";
    extraConfig = {
      pull.rebase = true;
      color.ui = true;
    };
  };
}
