{
  programs.git = {
    enable = true;
    settings = {
      user = {
        email = "DumbPuppy208@gmail.com";
        name = "Elise Corvidae";
      };
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
