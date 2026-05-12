#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${VIDEO_QA_CONDA_ENV:-video-qa-molmo}"

cleanup() {
  for pid in $(jobs -p); do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT

eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

cd "$ROOT_DIR/server"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &

cd "$ROOT_DIR/web"
if [ -s "$HOME/.nvm/nvm.sh" ]; then
  # shellcheck source=/dev/null
  source "$HOME/.nvm/nvm.sh"
  nvm use
fi
if [ ! -d node_modules ]; then
  npm install
fi
npm run dev
