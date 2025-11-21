{
  programs.git = {
    enable = true;
    userEmail = "matthew.michal11@gmail.com";
    userName = "Matthew Michal";
    settings = {
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
