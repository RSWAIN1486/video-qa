#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export VIDEO_QA_DATA_DIR="${VIDEO_QA_DATA_DIR:-$ROOT_DIR/data}"
export HF_HOME="${HF_HOME:-$ROOT_DIR/data/huggingface}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-$HF_HOME/hub}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$HF_HOME/transformers}"

mkdir -p "$VIDEO_QA_DATA_DIR" "$HF_HOME" "$HUGGINGFACE_HUB_CACHE" "$TRANSFORMERS_CACHE"
