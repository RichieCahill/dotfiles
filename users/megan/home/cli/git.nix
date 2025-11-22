{
  programs.git = {
    enable = true;
    settings = {
      user = {
        email= "mousikos112@gmail.com";
        name= "megan";
      };
      pull.rebase = true;
      color.ui = true;
    };
    lfs.enable = true;
  };
}
