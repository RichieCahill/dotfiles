{
  programs.git = {
    enable = true;
    userEmail = "mousikos112@gmail.com";
    userName = "megan";
    extraConfig = {
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
