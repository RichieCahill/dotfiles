#!/usr/bin/env bash
# Fine-tune Qwen 3.5 4B on bill summarization data.
#
# Prerequisites:
#   1. Build the dataset:  python -m python.prompt_bench.build_finetune_dataset
#   2. Build the image:    docker build -f python/prompt_bench/Dockerfile.finetune -t bill-finetune .
#
# Usage:
#   bash python/prompt_bench/train.sh [extra flags passed to finetune.py]
#
# Examples:
#   bash python/prompt_bench/train.sh
#   bash python/prompt_bench/train.sh --epochs 5 --lr 1e-4
#   bash python/prompt_bench/train.sh --val-split 0.15 --save-gguf

set -euo pipefail

IMAGE="bill-finetune"
DATASET="$(pwd)/output/finetune_dataset.jsonl"
OUTPUT_DIR="$(pwd)/output/qwen-bill-summarizer"

if [ ! -f "$DATASET" ]; then
    echo "Error: Dataset not found at $DATASET"
    echo "Run: python -m python.prompt_bench.build_finetune_dataset"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Starting fine-tuning..."
echo "  Dataset:    $DATASET"
echo "  Output:     $OUTPUT_DIR"
echo "  Extra args: $*"

docker run --rm \
    --device=nvidia.com/gpu=all \
    --ipc=host \
    -v "$OUTPUT_DIR":/workspace/output/qwen-bill-summarizer \
    -v "$DATASET":/workspace/dataset.jsonl:ro \
    "$IMAGE" \
    --dataset /workspace/dataset.jsonl \
    --output-dir /workspace/output/qwen-bill-summarizer \
    "$@"

echo "Done! Model saved to $OUTPUT_DIR"
