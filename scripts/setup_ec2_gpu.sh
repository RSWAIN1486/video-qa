#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${VIDEO_QA_CONDA_ENV:-video-qa-molmo}"

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi was not found. Use an NVIDIA GPU AMI or install NVIDIA drivers first."
  exit 1
fi

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y ffmpeg
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

python - <<'PY'
import torch
print("cuda_available=", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device=", torch.cuda.get_device_name(0))
PY

echo "EC2 GPU setup complete. Run scripts/run_api_ec2.sh from this repo."

