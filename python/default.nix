{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    python313.withPackages
    (
      ps: with ps; [
        apprise
        apscheduler
        mypy
        polars
        pyfakefs
        pytest
        pytest-cov
        pytest-mock
        pytest-xdist
        requests
        ruff
        typer
        types-requests
      ]
    )
  ];
}
