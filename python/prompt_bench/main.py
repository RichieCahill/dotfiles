"""CLI entry point for the prompt benchmarking system."""

from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Annotated

import typer

from python.prompt_bench.containers.lib import check_gpu_free
from python.prompt_bench.containers.vllm import start_vllm, stop_vllm
from python.prompt_bench.downloader import is_model_present
from python.prompt_bench.models import BenchmarkConfig
from python.prompt_bench.vllm_client import VLLMClient

logger = logging.getLogger(__name__)


def discover_prompts(input_dir: Path) -> list[Path]:
    """Find all .txt files in the input directory."""
    prompts = list(input_dir.glob("*.txt"))
    if not prompts:
        message = f"No .txt files found in {input_dir}"
        raise FileNotFoundError(message)
    return prompts


def _run_prompt(
    client: VLLMClient,
    prompt_path: Path,
    *,
    repo: str,
    model_dir_name: str,
    model_output: Path,
    temperature: float,
) -> tuple[bool, float]:
    """Run a single prompt. Returns (success, elapsed_seconds)."""
    filename = prompt_path.name
    output_path = model_output / filename
    start = time.monotonic()
    try:
        prompt_text = prompt_path.read_text()
        response = client.complete(prompt_text, model_dir_name, temperature=temperature)
        output_path.write_text(response)
        elapsed = time.monotonic() - start
        logger.info("Completed: %s / %s in %.2fs", repo, filename, elapsed)
    except Exception:
        elapsed = time.monotonic() - start
        error_path = model_output / f"{filename}.error"
        logger.exception("Failed: %s / %s after %.2fs", repo, filename, elapsed)
        error_path.write_text(f"Error processing {filename}")
        return False, elapsed
    return True, elapsed


def benchmark_model(
    client: VLLMClient,
    prompts: list[Path],
    *,
    repo: str,
    model_dir_name: str,
    model_output: Path,
    temperature: float,
    concurrency: int,
) -> tuple[int, int]:
    """Run all prompts against a single model in parallel.

    vLLM batches concurrent requests internally, so submitting many at once is
    significantly faster than running them serially.
    """
    pending = [prompt for prompt in prompts if not (model_output / prompt.name).exists()]
    skipped = len(prompts) - len(pending)
    if skipped:
        logger.info("Skipping %d prompts with existing output for %s", skipped, repo)

    if not pending:
        logger.info("Nothing to do for %s", repo)
        return 0, 0

    completed = 0
    failed = 0
    latencies: list[float] = []

    wall_start = time.monotonic()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(
                _run_prompt,
                client,
                prompt_path,
                repo=repo,
                model_dir_name=model_dir_name,
                model_output=model_output,
                temperature=temperature,
            )
            for prompt_path in pending
        ]
        for future in as_completed(futures):
            success, elapsed = future.result()
            latencies.append(elapsed)
            if success:
                completed += 1
            else:
                failed += 1
    wall_elapsed = time.monotonic() - wall_start

    attempted = completed + failed
    avg_latency = sum(latencies) / attempted
    throughput = attempted / wall_elapsed if wall_elapsed > 0 else 0.0
    timing = {
        "repo": repo,
        "wall_seconds": wall_elapsed,
        "attempted": attempted,
        "completed": completed,
        "failed": failed,
        "avg_latency_seconds": avg_latency,
        "throughput_prompts_per_second": throughput,
        "concurrency": concurrency,
    }
    timing_path = model_output / "_timing.json"
    timing_path.write_text(json.dumps(timing, indent=2))

    return completed, failed


def run_benchmark(
    config: BenchmarkConfig,
    input_dir: Path,
    output_dir: Path,
) -> None:
    """Execute the benchmark across all models and prompts."""
    prompts = discover_prompts(input_dir)
    logger.info("Found %d prompts in %s", len(prompts), input_dir)

    check_gpu_free()

    total_completed = 0
    total_failed = 0

    for repo in config.models:
        if not is_model_present(repo, config.model_dir):
            logger.warning("Skipping (not downloaded): %s", repo)
            continue

        model_output = output_dir / repo
        model_output.mkdir(parents=True, exist_ok=True)

        logger.info("=== Benchmarking model: %s ===", repo)

        stop_vllm()
        try:
            start_vllm(
                model=repo,
                port=config.port,
                model_dir=config.model_dir,
                gpu_memory_utilization=config.gpu_memory_utilization,
            )
        except RuntimeError:
            logger.exception("Failed to start vLLM for %s, skipping", repo)
            continue
        logger.info("vLLM started for %s", repo)
        try:
            with VLLMClient(port=config.port, timeout=config.timeout) as client:
                client.wait_ready(max_wait=config.vllm_startup_timeout)
                completed, failed = benchmark_model(
                    client,
                    prompts,
                    repo=repo,
                    model_dir_name=repo,
                    model_output=model_output,
                    temperature=config.temperature,
                    concurrency=config.concurrency,
                )
                total_completed += completed
                total_failed += failed
        finally:
            stop_vllm()

    logger.info("=== Benchmark complete ===")
    logger.info("Completed: %d | Failed: %d", total_completed, total_failed)


def main(
    input_dir: Annotated[Path, typer.Argument(help="Directory containing input .txt prompt files")],
    config: Annotated[Path, typer.Option(help="Path to TOML config file")] = Path("bench.toml"),
    output_dir: Annotated[Path, typer.Option(help="Output directory for results")] = Path("output"),
    log_level: Annotated[str, typer.Option(help="Log level")] = "INFO",
) -> None:
    """Run prompts through multiple LLMs via vLLM and save results."""
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if not input_dir.is_dir():
        message = f"Input directory does not exist: {input_dir}"
        raise typer.BadParameter(message)
    if not config.is_file():
        message = f"Config file does not exist: {config}"
        raise typer.BadParameter(message)

    benchmark_config = BenchmarkConfig.from_toml(config)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_benchmark(benchmark_config, input_dir, output_dir)


def cli() -> None:
    """Typer entry point."""
    typer.run(main)


if __name__ == "__main__":
    cli()
