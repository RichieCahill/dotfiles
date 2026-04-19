{
  programs.git = {
    enable = true;
    signing.format = null;
    settings = {
      user = {
        email = "matthew.michal11@gmail.com";
        name = "Matthew Michal";
      };
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
