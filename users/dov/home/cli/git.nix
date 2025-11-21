{
  programs.git = {
    enable = true;
    userEmail = "dov.kruger@gmail.com";
    userName = "Dov Kruger";
    settings = {
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
