{
  programs.git = {
    enable = true;
    userEmail = "dov.kruger@gmail.com";
    userName = "Dov Kruger";
    extraConfig = {
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
