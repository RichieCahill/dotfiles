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
from pathlib import Path
from typing import Annotated

import typer
from unsloth import FastLanguageModel
from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer

logger = logging.getLogger(__name__)

BASE_MODEL = "unsloth/Qwen3-4B-Base-unsloth-bnb-4bit"

# LoRA hyperparameters
LORA_RANK = 32
LORA_ALPHA = 32
LORA_DROPOUT = 0.0
LORA_TARGETS = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]

# Training hyperparameters tuned for ~2k examples on a 3090
LEARNING_RATE = 2e-4
EPOCHS = 3
BATCH_SIZE = 2
GRADIENT_ACCUMULATION = 8  # effective batch = 16
MAX_SEQ_LENGTH = 4096
WARMUP_RATIO = 0.05
WEIGHT_DECAY = 0.01
LOGGING_STEPS = 10
SAVE_STEPS = 100


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
    base_model: Annotated[str, typer.Option("--base-model", help="Unsloth model ID")] = BASE_MODEL,
    epochs: Annotated[int, typer.Option("--epochs", help="Training epochs")] = EPOCHS,
    batch_size: Annotated[int, typer.Option("--batch-size", help="Per-device batch size")] = BATCH_SIZE,
    learning_rate: Annotated[float, typer.Option("--lr", help="Learning rate")] = LEARNING_RATE,
    lora_rank: Annotated[int, typer.Option("--lora-rank", help="LoRA rank")] = LORA_RANK,
    max_seq_length: Annotated[int, typer.Option("--max-seq-length", help="Max sequence length")] = MAX_SEQ_LENGTH,
    save_gguf: Annotated[bool, typer.Option("--save-gguf/--no-save-gguf", help="Also save GGUF")] = False,
) -> None:
    """Fine-tune Qwen 3.5 4B on bill summarization with Unsloth + QLoRA."""
    logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if not dataset_path.is_file():
        message = f"Dataset not found: {dataset_path}"
        raise typer.BadParameter(message)

    logger.info("Loading base model: %s", base_model)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq_length,
        load_in_4bit=True,
        dtype=None,
    )

    logger.info("Applying LoRA (rank=%d, alpha=%d)", lora_rank, LORA_ALPHA)
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_rank,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGETS,
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
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=learning_rate,
        warmup_ratio=WARMUP_RATIO,
        weight_decay=WEIGHT_DECAY,
        lr_scheduler_type="cosine",
        logging_steps=LOGGING_STEPS,
        save_steps=SAVE_STEPS,
        save_total_limit=3,
        eval_strategy="steps",
        eval_steps=SAVE_STEPS,
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
        max_seq_length=max_seq_length,
        packing=True,
    )

    logger.info("Starting training: %d train, %d val, %d epochs", len(train_dataset), len(validation_dataset), epochs)
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
