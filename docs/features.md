# Features

## V1 Demo

- Select the included `test1.mp4` sample or upload a short MP4, MOV, or WebM clip.
- Show visible uploading and loaded states for the selected video.
- Preview the selected video directly in the browser.
- Ask natural-language questions in a chat-style interface.
- Parse model pointing outputs, hide raw coordinate tags from answers, and show a marker on the video when a point is returned.
- Use sample prompts for a quick client-ready flow:
  - `what do you see in the video`
  - `when did the woman in red turn backward`
- Stream run status and final answers with Server-Sent Events.
- Show model status, cold-start state, device, and errors.
- Warm-load Molmo2-8B from the header before asking the first question.
- Log QA progress in the backend terminal, including model load, video preprocessing, generation, final latency, and answer preview.
- Persist video metadata and QA history in SQLite.

## Model Runtime

- Uses `allenai/Molmo2-8B` with native video input through Transformers.
- Lazy-loads the model on first QA request.
- Serializes inference to protect local/GPU memory.
- Defaults to short videos up to 60 seconds and 200 MB.

## Local-First Guarantees

- Uploaded videos remain on the machine or private EC2 host running the app.
- Runtime state is stored under `data/`.
- Public URL, DNS, HTTPS, and client authentication are intentionally out of scope for the first screen-share demo.

## Planned Next Step

Long-video support will add chunking, per-chunk summaries, and retrieval over temporal segments while preserving the same upload and QA surface.
