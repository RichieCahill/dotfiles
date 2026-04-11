"""Fine-tune Qwen 3.5 4B on bill summarization data using Unsloth.

Loads a ChatML-style JSONL dataset (system/user/assistant messages),
applies QLoRA with 4-bit quantization, and saves the merged model
in HuggingFace format. Designed for a single RTX 3090 (24GB).

Usage:
    python -m python.prompt_bench.finetune \
        --dataset output/finetune_dataset.jsonl \
        --output-dir output/qwen-bill-summarizer
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import tomllib
import typer
from unsloth import FastLanguageModel
from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer

logger = logging.getLogger(__name__)


@dataclass
class LoraConfig:
    """LoRA adapter hyperparameters."""

    rank: int
    alpha: int
    dropout: float
    targets: list[str]


@dataclass
class TrainingConfig:
    """Training loop hyperparameters."""

    learning_rate: float
    epochs: int
    batch_size: int
    gradient_accumulation: int
    max_seq_length: int
    warmup_ratio: float
    weight_decay: float
    logging_steps: int
    save_steps: int


@dataclass
class FinetuneConfig:
    """Top-level finetune configuration."""

    base_model: str
    lora: LoraConfig
    training: TrainingConfig

    @classmethod
    def from_toml(cls, config_path: Path) -> FinetuneConfig:
        """Load finetune config from a TOML file."""
        raw = tomllib.loads(config_path.read_text())["finetune"]
        return cls(
            base_model=raw["base_model"],
            lora=LoraConfig(**raw["lora"]),
            training=TrainingConfig(**raw["training"]),
        )


def _messages_to_chatml(messages: list[dict]) -> str:
    r"""Convert a message list to Qwen ChatML format.

    Produces:
        <|im_start|>system\n...\n<|im_end|>
        <|im_start|>user\n...\n<|im_end|>
        <|im_start|>assistant\n...\n<|im_end|>
    """
    parts = []
    for message in messages:
        role = message["role"]
        content = message["content"]
        parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
    return "\n".join(parts)


def load_dataset_from_jsonl(path: Path) -> Dataset:
    """Load a ChatML JSONL file into a HuggingFace Dataset.

    Each line must have {"messages": [{"role": ..., "content": ...}, ...]}.
    Pre-formats into a `text` column with the Qwen ChatML template applied,
    which SFTTrainer consumes directly.
    """
    records = []
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            if stripped:
                entry = json.loads(stripped)
                records.append({"text": _messages_to_chatml(entry["messages"])})
    logger.info("Loaded %d examples from %s", len(records), path)
    return Dataset.from_list(records)


def main(
    dataset_path: Annotated[Path, typer.Option("--dataset", help="Fine-tuning JSONL")] = Path(
        "output/finetune_dataset.jsonl",
    ),
    validation_split: Annotated[float, typer.Option("--val-split", help="Fraction held out for validation")] = 0.1,
    output_dir: Annotated[Path, typer.Option("--output-dir", help="Where to save the merged model")] = Path(
        "output/qwen-bill-summarizer",
    ),
    config_path: Annotated[
        Path,
        typer.Option("--config", help="TOML config file"),
    ] = Path(__file__).parent / "config.toml",
    save_gguf: Annotated[bool, typer.Option("--save-gguf/--no-save-gguf", help="Also save GGUF")] = False,
) -> None:
    """Fine-tune Qwen 3.5 4B on bill summarization with Unsloth + QLoRA."""
    logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if not dataset_path.is_file():
        message = f"Dataset not found: {dataset_path}"
        raise typer.BadParameter(message)

    config = FinetuneConfig.from_toml(config_path)

    logger.info("Loading base model: %s", config.base_model)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config.base_model,
        max_seq_length=config.training.max_seq_length,
        load_in_4bit=True,
        dtype=None,
    )

    logger.info("Applying LoRA (rank=%d, alpha=%d)", config.lora.rank, config.lora.alpha)
    model = FastLanguageModel.get_peft_model(
        model,
        r=config.lora.rank,
        lora_alpha=config.lora.alpha,
        lora_dropout=config.lora.dropout,
        target_modules=config.lora.targets,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    full_dataset = load_dataset_from_jsonl(dataset_path)
    split = full_dataset.train_test_split(test_size=validation_split, seed=42)
    train_dataset = split["train"]
    validation_dataset = split["test"]
    logger.info("Split: %d train, %d validation", len(train_dataset), len(validation_dataset))
    training_args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=config.training.epochs,
        per_device_train_batch_size=config.training.batch_size,
        gradient_accumulation_steps=config.training.gradient_accumulation,
        learning_rate=config.training.learning_rate,
        warmup_ratio=config.training.warmup_ratio,
        weight_decay=config.training.weight_decay,
        lr_scheduler_type="cosine",
        logging_steps=config.training.logging_steps,
        save_steps=config.training.save_steps,
        save_total_limit=3,
        eval_strategy="steps",
        eval_steps=config.training.save_steps,
        load_best_model_at_end=True,
        bf16=True,
        optim="adamw_8bit",
        seed=42,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        args=training_args,
        max_seq_length=config.training.max_seq_length,
        packing=True,
    )

    logger.info(
        "Starting training: %d train, %d val, %d epochs",
        len(train_dataset),
        len(validation_dataset),
        config.training.epochs,
    )
    trainer.train()

    merged_path = str(output_dir / "merged")
    logger.info("Saving merged model to %s", merged_path)
    model.save_pretrained_merged(merged_path, tokenizer, save_method="merged_16bit")

    if save_gguf:
        gguf_path = str(output_dir / "gguf")
        logger.info("Saving GGUF to %s", gguf_path)
        model.save_pretrained_gguf(gguf_path, tokenizer, quantization_method="q4_k_m")

    logger.info("Done! Model saved to %s", output_dir)


def cli() -> None:
    """Typer entry point."""
    typer.run(main)


if __name__ == "__main__":
    cli()
