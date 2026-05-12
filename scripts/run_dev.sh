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
NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  # shellcheck source=/dev/null
  source "$NVM_DIR/nvm.sh"
  nvm use
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "npm is not available. Run ./scripts/setup_ec2_gpu.sh first, or install Node $(cat .nvmrc) with nvm."
  exit 1
fi
if [ ! -d node_modules ]; then
  npm install
fi
npm run dev
