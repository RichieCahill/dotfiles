{ inputs, ... }:
{
  # When applied, the stable nixpkgs set (declared in the flake inputs) will be accessible through 'pkgs.stable'
  stable = final: _prev: {
    stable = import inputs.nixpkgs-stable {
      system = final.stdenv.hostPlatform.system;
      config.allowUnfree = true;
    };
  };
  # When applied, the master nixpkgs set (declared in the flake inputs) will be accessible through 'pkgs.master'
  master = final: _prev: {
    master = import inputs.nixpkgs-master {
      system = final.stdenv.hostPlatform.system;
      config.allowUnfree = true;
    };
  };

  python-env = final: _prev: {
    my_python = final.python314.withPackages (
      ps: with ps; [
        alembic
        apprise
        apscheduler
        fastapi
        fastapi-cli
        httpx
        mypy
        polars
        psycopg
        pydantic
        pyfakefs
        pytest
        pytest-cov
        pytest-mock
        pytest-xdist
        requests
        ruff
        scalene
        sqlalchemy
        sqlalchemy
        textual
        tinytuya
        typer
        types-requests
      ]
    );
  };
}
