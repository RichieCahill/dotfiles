{
  programs.git = {
    enable = true;
    userEmail = "DumbPuppy208@gmail.com";
    userName = "Elise Corvidae";
    extraConfig = {
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
