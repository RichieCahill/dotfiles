{
  programs.git = {
    enable = true;
    settings = {
      user = {
        email = "dov.kruger@gmail.com";
        name = "Dov Kruger";
      };
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
