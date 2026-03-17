import zipfile
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from python.sheet_music_ocr.audiveris import AudiverisError, find_audiveris, run_audiveris
from python.sheet_music_ocr.main import SUPPORTED_EXTENSIONS, app, extract_mxml_from_mxl

runner = CliRunner()


def make_mxl(path, xml_content=b"<score-partwise/>"):
    """Create a minimal .mxl (ZIP) file with a MusicXML inside."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("score.xml", xml_content)


class TestExtractMxmlFromMxl:
    def test_extracts_xml(self, tmp_path):
        mxl = tmp_path / "test.mxl"
        output = tmp_path / "output.mxml"
        content = b"<score-partwise>hello</score-partwise>"
        make_mxl(mxl, content)

        result = extract_mxml_from_mxl(mxl, output)

        assert result == output
        assert output.read_bytes() == content

    def test_skips_meta_inf(self, tmp_path):
        mxl = tmp_path / "test.mxl"
        output = tmp_path / "output.mxml"
        with zipfile.ZipFile(mxl, "w") as zf:
            zf.writestr("META-INF/container.xml", "<container/>")
            zf.writestr("score.xml", b"<score/>")

        extract_mxml_from_mxl(mxl, output)

        assert output.read_bytes() == b"<score/>"

    def test_raises_when_no_xml(self, tmp_path):
        mxl = tmp_path / "test.mxl"
        output = tmp_path / "output.mxml"
        with zipfile.ZipFile(mxl, "w") as zf:
            zf.writestr("readme.txt", "no xml here")

        with pytest.raises(FileNotFoundError, match="No MusicXML"):
            extract_mxml_from_mxl(mxl, output)


class TestFindAudiveris:
    def test_raises_when_not_found(self):
        with (
            patch("python.sheet_music_ocr.audiveris.shutil.which", return_value=None),
            pytest.raises(AudiverisError, match="not found"),
        ):
            find_audiveris()

    def test_returns_path_when_found(self):
        with patch("python.sheet_music_ocr.audiveris.shutil.which", return_value="/usr/bin/audiveris"):
            assert find_audiveris() == "/usr/bin/audiveris"


class TestRunAudiveris:
    def test_raises_on_nonzero_exit(self, tmp_path):
        with (
            patch("python.sheet_music_ocr.audiveris.find_audiveris", return_value="audiveris"),
            patch("python.sheet_music_ocr.audiveris.subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "something went wrong"

            with pytest.raises(AudiverisError, match="failed"):
                run_audiveris(tmp_path / "input.pdf", tmp_path / "output")

    def test_raises_when_no_mxl_produced(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with (
            patch("python.sheet_music_ocr.audiveris.find_audiveris", return_value="audiveris"),
            patch("python.sheet_music_ocr.audiveris.subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0

            with pytest.raises(AudiverisError, match=r"no \.mxl output"):
                run_audiveris(tmp_path / "input.pdf", output_dir)

    def test_returns_mxl_path(self, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        mxl = output_dir / "score.mxl"
        make_mxl(mxl)

        with (
            patch("python.sheet_music_ocr.audiveris.find_audiveris", return_value="audiveris"),
            patch("python.sheet_music_ocr.audiveris.subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0

            result = run_audiveris(tmp_path / "input.pdf", output_dir)
            assert result == mxl


class TestCli:
    def test_missing_input_file(self, tmp_path):
        result = runner.invoke(app, [str(tmp_path / "nonexistent.pdf")])
        assert result.exit_code == 1
        assert "does not exist" in result.output

    def test_unsupported_format(self, tmp_path):
        bad_file = tmp_path / "music.bmp"
        bad_file.touch()
        result = runner.invoke(app, [str(bad_file)])
        assert result.exit_code == 1
        assert "Unsupported format" in result.output

    def test_supported_extensions_complete(self):
        assert ".pdf" in SUPPORTED_EXTENSIONS
        assert ".png" in SUPPORTED_EXTENSIONS
        assert ".jpg" in SUPPORTED_EXTENSIONS
        assert ".jpeg" in SUPPORTED_EXTENSIONS
        assert ".tiff" in SUPPORTED_EXTENSIONS

    def test_successful_conversion(self, tmp_path):
        input_file = tmp_path / "score.pdf"
        input_file.touch()
        output_file = tmp_path / "score.mxml"

        mxl_path = tmp_path / "tmp_mxl" / "score.mxl"
        mxl_path.parent.mkdir()
        make_mxl(mxl_path, b"<score-partwise/>")

        with patch("python.sheet_music_ocr.main.run_audiveris", return_value=mxl_path):
            result = runner.invoke(app, [str(input_file), "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        assert "Written" in result.output

    def test_default_output_path(self, tmp_path):
        input_file = tmp_path / "score.png"
        input_file.touch()

        mxl_path = tmp_path / "tmp_mxl" / "score.mxl"
        mxl_path.parent.mkdir()
        make_mxl(mxl_path)

        with patch("python.sheet_music_ocr.main.run_audiveris", return_value=mxl_path):
            result = runner.invoke(app, [str(input_file)])

        assert result.exit_code == 0
        assert (tmp_path / "score.mxml").exists()
