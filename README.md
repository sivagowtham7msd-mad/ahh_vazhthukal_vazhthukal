# Retail Theft Detection Demo (Laptop Camera)

This is a runnable demo backend using **FastAPI + OpenCV + MediaPipe**.

## Project reference
We are using your shared product-overview reference as the direction for iterative development:
- https://youtu.be/RRlgmT3lSPw?si=VKx41VyCmLzNJBjW

This repository currently implements the **MVP backend layer** (camera ingest + pose features + risk scoring + live API streams) so we can keep improving toward the full product vision.

## What it does
- Opens your laptop camera (`camera_id=0` by default)
- Runs a simple pose-based suspicious-motion heuristic
- Overlays risk score on video frames
- Streams video via `/video_feed`
- Sends alert events via WebSocket `/ws/alerts`

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open:
- `http://localhost:8000/health`
- `http://localhost:8000/video_feed`

WebSocket alerts:
- `ws://localhost:8000/ws/alerts`

## Notes
- This is a **demo heuristic**, not production-grade theft detection.
- You should calibrate per-store zones, tracking, and checkout correlation for real deployments.

## Next implementation steps (aligned with product overview)
1. Add multi-camera management with persistent camera configs.
2. Add person tracking IDs and zone-aware logic (shelf/checkout/exit).
3. Save alert clips + metadata to database/object storage.
4. Add reviewer dashboard and feedback loop to reduce false positives.
5. Add model/rule tuning from real in-store datasets.
