#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=env.sh
source "$ROOT_DIR/scripts/env.sh"
ENV_NAME="${VIDEO_QA_CONDA_ENV:-video-qa-molmo}"

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is required. Install Miniconda or make conda available in PATH."
  exit 1
fi

if ! command -v ffprobe >/dev/null 2>&1; then
  echo "ffmpeg/ffprobe is required. On macOS: brew install ffmpeg"
  exit 1
fi

if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  conda create -y -n "$ENV_NAME" python=3.11
fi

eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"
python -m pip install --upgrade pip
python -m pip install -r "$ROOT_DIR/server/requirements-dev.txt"

if [ -s "$HOME/.nvm/nvm.sh" ]; then
  # shellcheck source=/dev/null
  source "$HOME/.nvm/nvm.sh"
  cd "$ROOT_DIR/web"
  nvm install
  nvm use
else
  echo "nvm not found; install Node $(cat "$ROOT_DIR/web/.nvmrc") or newer before running the WebUI."
fi

echo "Local setup complete."
