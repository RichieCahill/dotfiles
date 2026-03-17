"""CLI tool for converting scanned sheet music to MusicXML.

Usage:
    sheet-music-ocr scan.pdf
    sheet-music-ocr scan.png -o output.mxml
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Annotated

import typer

from python.sheet_music_ocr.audiveris import AudiverisError, run_audiveris

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}

app = typer.Typer(help="Convert scanned sheet music to MusicXML using Audiveris.")


def extract_mxml_from_mxl(mxl_path: Path, output_path: Path) -> Path:
    """Extract the MusicXML file from an .mxl archive.

    An .mxl file is a ZIP archive containing one or more .xml MusicXML files.

    Args:
        mxl_path: Path to the .mxl file.
        output_path: Path where the extracted .mxml file should be written.

    Returns:
        The output path.

    Raises:
        FileNotFoundError: If no MusicXML file is found inside the archive.
    """
    with zipfile.ZipFile(mxl_path, "r") as zf:
        xml_names = [n for n in zf.namelist() if n.endswith(".xml") and not n.startswith("META-INF")]
        if not xml_names:
            msg = f"No MusicXML (.xml) file found inside {mxl_path}"
            raise FileNotFoundError(msg)
        with zf.open(xml_names[0]) as src, output_path.open("wb") as dst:
            dst.write(src.read())
    return output_path


@app.command()
def convert(
    input_file: Annotated[Path, typer.Argument(help="Path to sheet music scan (PDF, PNG, JPG, TIFF).")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output .mxml file path. Defaults to <input_stem>.mxml."),
    ] = None,
) -> None:
    """Convert a scanned sheet music file to MusicXML."""
    if not input_file.exists():
        typer.echo(f"Error: {input_file} does not exist.", err=True)
        raise typer.Exit(code=1)

    if input_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
        typer.echo(
            f"Error: Unsupported format '{input_file.suffix}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            err=True,
        )
        raise typer.Exit(code=1)

    output_path = output or input_file.with_suffix(".mxml")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            mxl_path = run_audiveris(input_file, Path(tmpdir))
        except AudiverisError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1) from e

        try:
            extract_mxml_from_mxl(mxl_path, output_path)
        except FileNotFoundError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1) from e

    typer.echo(f"Written: {output_path}")


if __name__ == "__main__":
    app()
