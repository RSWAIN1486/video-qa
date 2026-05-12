#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${VIDEO_QA_CONDA_ENV:-video-qa-molmo}"

eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

cd "$ROOT_DIR/server"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

