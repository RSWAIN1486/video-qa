#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export VIDEO_QA_DATA_DIR="${VIDEO_QA_DATA_DIR:-$ROOT_DIR/data}"
export HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-$HF_HOME/hub}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$HF_HOME/transformers}"

mkdir -p "$VIDEO_QA_DATA_DIR" "$HF_HOME" "$HUGGINGFACE_HUB_CACHE" "$TRANSFORMERS_CACHE"

if [ ! -w "$HF_HOME" ] || [ ! -w "$HUGGINGFACE_HUB_CACHE" ] || [ ! -w "$TRANSFORMERS_CACHE" ]; then
  echo "Fixing Hugging Face cache ownership under $HF_HOME"
  if command -v sudo >/dev/null 2>&1; then
    sudo chown -R "$USER:$USER" "$HF_HOME"
  else
    chown -R "$USER:$USER" "$HF_HOME"
  fi
fi

chmod -R u+rwX "$HF_HOME"
