{ inputs, ... }:
{
  # When applied, the stable nixpkgs set (declared in the flake inputs) will be accessible through 'pkgs.stable'
  stable = final: _prev: {
    stable = import inputs.nixpkgs-stable {
      system = final.system;
      config.allowUnfree = true;
    };
  };
  # When applied, the master nixpkgs set (declared in the flake inputs) will be accessible through 'pkgs.master'
  master = final: _prev: {
    master = import inputs.nixpkgs-master {
      system = final.system;
      config.allowUnfree = true;
    };
  };

  python-env = final: _prev: {
    my_python = final.python313.withPackages (
      ps: with ps; [
        apprise
        apscheduler
        mypy
        polars
        psycopg
        pyfakefs
        pytest
        pytest-cov
        pytest-mock
        pytest-xdist
        requests
        ruff
        scalene
        sqlalchemy
        textual
        typer
        types-requests
      ]
    );
  };
}
