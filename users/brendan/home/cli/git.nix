{
  programs.git = {
    enable = true;
    userEmail = "XXXXXXXXXXXXXXXXX";
    userName = "XXXXXXXXXXXXXXXXX";
    extraConfig = {
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
