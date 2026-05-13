#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=env.sh
source "$ROOT_DIR/scripts/env.sh"

ENV_NAME="${VIDEO_QA_CONDA_ENV:-video-qa-molmo}"
MODEL_ID="${VIDEO_QA_MODEL_ID:-allenai/Molmo2-8B}"
CACHE_DIR="$HUGGINGFACE_HUB_CACHE/models--${MODEL_ID//\//--}"

if [ -d "$CACHE_DIR/snapshots" ] && find "$CACHE_DIR/snapshots" -mindepth 1 -maxdepth 1 -type d | grep -q .; then
  echo "Model already appears downloaded:"
  du -sh "$CACHE_DIR" || true
  find "$CACHE_DIR" -maxdepth 3 -type f | head
  exit 0
fi

if ! command -v conda >/dev/null 2>&1; then
  if [ -x "$HOME/miniconda3/bin/conda" ]; then
    export PATH="$HOME/miniconda3/bin:$PATH"
  else
    echo "conda is required. Run ./scripts/setup_ec2_gpu.sh first."
    exit 1
  fi
fi

eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

python - <<'PY'
import os
from huggingface_hub import snapshot_download

model_id = os.environ.get("VIDEO_QA_MODEL_ID", "allenai/Molmo2-8B")
path = snapshot_download(model_id)
print("downloaded to:", path)
PY

echo "Model cache size:"
du -sh "$CACHE_DIR" || true
