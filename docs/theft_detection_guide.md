# Smart Theft Detection for Retail (Python + OpenCV + MediaPipe + FastAPI)

## 0) Reference and scope
This guide is aligned with your product-overview reference video:
- https://youtu.be/RRlgmT3lSPw?si=VKx41VyCmLzNJBjW

Use this document as the engineering blueprint while iterating toward that product direction.

---

## 1) What you are building
A practical theft-detection pipeline combines **video understanding**, **behavioral rules**, and **real-time alerting**:

1. **Ingest** RTSP/CCTV feeds.
2. **Detect people and products/shelves/zones** in frames.
3. **Track people** across frames.
4. **Estimate pose/hands** to infer suspicious actions (e.g., concealment near torso/bag, shelf interaction followed by exit without checkout-zone visit).
5. **Score risk** over a time window.
6. **Expose events and live status APIs** with FastAPI.
7. **Store evidence clips** and metadata for review.

> Important: Treat this as an **assistive alerting system** (not autonomous accusation). Keep a human-in-the-loop and implement privacy safeguards.

---

## 2) Recommended architecture

```text
Camera Streams (RTSP)
    -> Frame Grabber Workers (OpenCV)
    -> Detector + Tracker (YOLO/other + ByteTrack/DeepSORT)
    -> Pose/Hand Analysis (MediaPipe)
    -> Event Engine (rules + risk score)
    -> FastAPI Service
         - REST/WebSocket for alerts
         - Review endpoints
    -> Storage
         - Postgres (events)
         - Redis (realtime state)
         - Object storage/local disk (clips)
```

### Why split this way?
- **OpenCV workers** keep video I/O and frame decoding off your API thread.
- **FastAPI** stays responsive for clients and dashboard.
- **Event engine** is independent, so you can upgrade rules/ML without changing API contracts.

---

## 3) Core computer vision stack

## A) Person + object detection
- Use a detector for:
  - person
  - basket/cart
  - store bag/backpack
  - key product classes (if feasible)
- Start with a pretrained model and add store-specific fine-tuning later.

## B) Multi-object tracking
- Track each person with a stable `track_id`.
- Maintain history:
  - positions
  - dwell time in zones
  - hand-to-shelf interactions

## C) MediaPipe pose/hands
- For each tracked person crop:
  - run `MediaPipe Pose` for body landmarks
  - run `MediaPipe Hands` for precise hand positions
- Derive signals:
  - hand near shelf
  - hand to torso/bag pocket area
  - repeated conceal-like motion
  - abrupt movement after interaction

---

## 4) Behavior/risk logic (what actually detects “theft risk”)
Avoid one-frame decisions. Use **temporal scoring**.

### Example rules (weighted)
- `+2`: hand enters shelf interaction zone.
- `+3`: item-sized motion from shelf to body/bag zone.
- `+2`: occluded hand + torso contact > N frames.
- `+2`: person skips checkout zone and heads to exit.
- `-3`: person clearly visits checkout zone.

Trigger levels:
- `score >= 5`: low-priority watchlist event
- `score >= 8`: high-priority alert

Use cooldown + hysteresis to prevent alert spam.

---

## 5) FastAPI backend design

## Suggested modules
- `app/main.py` – FastAPI app, startup/shutdown.
- `app/api/events.py` – REST endpoints (`/events`, `/alerts`, `/clips/{id}`).
- `app/api/ws.py` – WebSocket push alerts.
- `app/vision/stream_worker.py` – camera frame readers.
- `app/vision/pipeline.py` – detect/track/pose orchestration.
- `app/engine/risk_engine.py` – scoring rules.
- `app/storage/repo.py` – DB operations.

## Suggested endpoints
- `GET /health`
- `GET /cameras`
- `POST /cameras/{id}/start`
- `POST /cameras/{id}/stop`
- `GET /events?camera_id=&severity=&from=&to=`
- `GET /events/{id}`
- `WS /ws/alerts`

---

## 6) Minimal pseudocode flow

```python
# vision loop (per camera)
while True:
    frame = read_frame()
    detections = detector(frame)
    tracks = tracker.update(detections)

    for t in tracks:
        person_crop = crop(frame, t.bbox)
        pose = mediapipe_pose(person_crop)
        hands = mediapipe_hands(person_crop)
        features = extract_behavior_features(t, pose, hands, zones)
        risk = risk_engine.update(track_id=t.id, features=features)

        if risk.alert:
            clip_path = save_clip(camera_buffer, t.id)
            event_id = save_event_db(camera_id, t.id, risk.score, clip_path)
            publish_alert(event_id)
```

---

## 7) Practical implementation tips

1. **Frame skipping**: run heavy inference every N frames (e.g., every 2–4) and interpolate tracks.
2. **ROI zones**: manually configure shelf/checkout/exit polygons per camera.
3. **Multi-processing**: dedicate one process per camera stream or per GPU batch.
4. **Clip ring buffer**: always keep last 15–30 seconds; on alert, dump pre/post windows.
5. **Calibration**: each store layout differs; tune thresholds per camera.
6. **False positives**: create a review tool and feedback loop to reweight rules.

---

## 8) Data model (starter)

### `events` table
- `id` (uuid)
- `camera_id`
- `track_id`
- `start_ts`, `end_ts`
- `risk_score`
- `severity`
- `rule_hits` (jsonb)
- `clip_url`
- `status` (`new`, `reviewed`, `dismissed`, `escalated`)

### `camera_state` (redis)
- current fps
- inference latency
- active track count
- latest alerts

---

## 9) Evaluation strategy (very important)
Measure quality before deployment:
- **Precision/Recall** on labeled incidents.
- **False alerts per hour per camera**.
- **Mean time to review** by staff.
- **Alert usefulness score** from operators.

Start with shadow mode:
1. Run silently for 2–4 weeks.
2. Collect false positives/negatives.
3. Tune thresholds/rules.
4. Only then enable live alerting.

---

## 10) Security, privacy, and compliance checklist
- Encrypt video in transit (RTSP over secure segment/VPN) and at rest.
- Role-based access to clips/events.
- Retention policy (auto-delete old footage).
- Face blurring for non-incident exports where required.
- Audit log for who viewed/downloaded evidence.
- Human review before any intervention.

---

## 11) Suggested build phases
1. **Phase 1**: camera ingestion + person tracking + zone analytics.
2. **Phase 2**: MediaPipe feature extraction + simple rule engine.
3. **Phase 3**: alert dashboard + evidence clips.
4. **Phase 4**: model/rule tuning with real store feedback.
5. **Phase 5**: multi-store scaling + observability.

---

## 12) Optional next step
If you want, I can turn this into a **starter FastAPI project structure** with:
- camera worker process
- MediaPipe feature extractor stub
- risk engine class
- PostgreSQL models
- REST + WebSocket endpoints
- Docker Compose for local testing
