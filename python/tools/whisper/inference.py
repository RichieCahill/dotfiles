"""Container entrypoint that transcribes a directory of audio files with faster-whisper.

Run inside the whisper-transcribe docker image; segment timestamps are grouped
into one-minute buckets so the output reads as ``[HH:MM:00] text``.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".mp4", ".mkv", ".webm", ".aac"}
BUCKET_SECONDS = 60
BEAM_SIZE = 5
SECONDS_PER_HOUR = 3600
SECONDS_PER_MINUTE = 60


def format_timestamp(total_seconds: float) -> str:
    """Render a whole-minute timestamp as ``HH:MM:00``.

    Args:
        total_seconds: Offset in seconds from the start of the audio.

    Returns:
        A zero-padded ``HH:MM:00`` string.
    """
    hours = int(total_seconds // SECONDS_PER_HOUR)
    minutes = int((total_seconds % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE)
    return f"{hours:02d}:{minutes:02d}:00"


def transcribe_file(model: WhisperModel, audio_path: Path, output_path: Path) -> None:
    """Transcribe one audio file and write the bucketed transcript to disk.

    Args:
        model: Loaded faster-whisper model.
        audio_path: Source audio file.
        output_path: Destination ``.txt`` path.
    """
    logger.info("Transcribing %s", audio_path)
    segments, info = model.transcribe(
        str(audio_path),
        language="en",
        beam_size=BEAM_SIZE,
        vad_filter=True,
    )
    logger.info("Duration %.1fs", info.duration)

    buckets: dict[int, list[str]] = {}
    for segment in segments:
        bucket = int(segment.start // BUCKET_SECONDS)
        buckets.setdefault(bucket, []).append(segment.text.strip())

    lines = [f"[{format_timestamp(bucket * BUCKET_SECONDS)}] {' '.join(buckets[bucket])}" for bucket in sorted(buckets)]
    output_path.write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Wrote %s", output_path)


def find_audio_files(input_directory: Path) -> list[Path]:
    """Collect every audio file under ``input_directory``.

    Args:
        input_directory: Directory to walk recursively.

    Returns:
        Sorted list of audio file paths.
    """
    return sorted(
        path for path in input_directory.rglob("*") if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    )


def configure_container_logger() -> None:
    """Configure logging for the container (stdout, INFO)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for the container entrypoint.

    Returns:
        Parsed argparse namespace.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("/audio"))
    parser.add_argument("--output", type=Path, default=Path("/output"))
    parser.add_argument("--model", default="large-v3")
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Download the model into the cache volume and exit without transcribing.",
    )
    return parser.parse_args()


def main() -> None:
    """Load the model, then either exit (download-only) or transcribe the directory."""
    configure_container_logger()
    arguments = parse_arguments()

    logger.info("Loading model %s on CUDA", arguments.model)
    model = WhisperModel(arguments.model, device="cuda", compute_type="float16")

    if arguments.download_only:
        logger.info("Model ready; exiting (download-only mode)")
        return

    arguments.output.mkdir(parents=True, exist_ok=True)

    audio_files = find_audio_files(arguments.input)
    if not audio_files:
        logger.warning("No audio files found in %s", arguments.input)
        return

    logger.info("Found %d audio file(s)", len(audio_files))
    for audio_path in audio_files:
        relative = audio_path.relative_to(arguments.input)
        output_path = arguments.output / relative.with_suffix(".txt")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            logger.info("Skip %s (already transcribed)", relative)
            continue
        transcribe_file(model, audio_path, output_path)


if __name__ == "__main__":
    main()
