#!/bin/bash
set -e

mkdir -p ./models
cd ./models

MODEL_URL="https://huggingface.co/bartowski/gemma-3-1b-it-GGUF/resolve/main/gemma-3-1b-it-Q4_K_M.gguf"
MODEL_FILE="gemma-3-1b-it-q4_k_m.gguf"

echo "Downloading $MODEL_FILE from Hugging Face..."
curl -L -o "$MODEL_FILE" "$MODEL_URL" --progress-bar

FILE_SIZE=$(stat -c%s "$MODEL_FILE" 2>/dev/null || stat -f%z "$MODEL_FILE")
if [ "$FILE_SIZE" -lt 500000000 ]; then
    echo "Error: Downloaded file is too small (less than 500MB). Download may have failed."
    exit 1
fi

echo "Model ready at ./models/$MODEL_FILE"