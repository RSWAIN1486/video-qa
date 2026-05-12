# Molmo2 Video QA Demo

A local-first browser demo for asking questions about short videos with `allenai/Molmo2-8B`.

The first version is built for screen-share demos: upload or select the included `test1.mp4`, ask natural-language questions, and stream the answer through a small FastAPI + SvelteKit app. Videos stay on the machine running the app. The only expected network use is downloading model/dependency artifacts.

## Quick Start

```bash
./scripts/setup_local_mac.sh
./scripts/run_dev.sh
```

Open `http://127.0.0.1:5173`.

If the Mac cannot load the model comfortably, run the same repo on the GPU EC2 host:

```bash
./scripts/setup_ec2_gpu.sh
./scripts/run_dev.sh
```

Then forward ports from your Mac:

```bash
ssh -L 8000:127.0.0.1:8000 -L 5173:127.0.0.1:5173 ubuntu@YOUR_EC2_HOST
```

## What Is Included

- Polished video QA WebUI with upload, preview, sample prompts, model status, and answer history.
- FastAPI backend with typed APIs, SSE answer streaming, SQLite persistence, and local file storage.
- Lazy Molmo2-8B inference through Transformers using native video input.
- Scripts for local Mac setup and private EC2 GPU demo runs.

## Docs

- [Architecture](docs/architecture.md)
- [Features](docs/features.md)
