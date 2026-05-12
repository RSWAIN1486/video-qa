#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${VIDEO_QA_CONDA_ENV:-video-qa-molmo}"
NODE_VERSION="$(cat "$ROOT_DIR/web/.nvmrc")"
NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
NVM_VERSION="${VIDEO_QA_NVM_VERSION:-v0.40.3}"

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi was not found. Use an NVIDIA GPU AMI or install NVIDIA drivers first."
  exit 1
fi

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y curl ca-certificates ffmpeg
fi

if ! command -v conda >/dev/null 2>&1; then
  echo "conda is required. Install Miniconda/Mambaforge on the EC2 host first."
  exit 1
fi

if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  conda create -y -n "$ENV_NAME" python=3.11
fi

eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"
python -m pip install --upgrade pip
python -m pip install -r "$ROOT_DIR/server/requirements-dev.txt"

if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  echo "Installing nvm into $NVM_DIR"
  curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh" | bash
fi

# shellcheck source=/dev/null
source "$NVM_DIR/nvm.sh"
nvm install "$NODE_VERSION"
nvm use "$NODE_VERSION"

cd "$ROOT_DIR/web"
npm install

python - <<'PY'
import torch
print("cuda_available=", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device=", torch.cuda.get_device_name(0))
PY

echo "EC2 GPU setup complete. Run scripts/run_dev.sh from this repo."
