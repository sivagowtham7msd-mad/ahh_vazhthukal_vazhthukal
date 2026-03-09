from __future__ import annotations

import asyncio
import threading
import time
from typing import Optional

import cv2

from app.risk import RiskEngine

try:
    import mediapipe as mp
except Exception:  # mediapipe optional at import-time
    mp = None


class CameraWorker:
    def __init__(self, camera_id: int = 0) -> None:
        self.camera_id = camera_id
        self.capture: Optional[cv2.VideoCapture] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.latest_jpeg: Optional[bytes] = None
        self.latest_state: dict = {"score": 0, "reason": "booting", "alert": False}
        self.alert_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=200)
        self.risk = RiskEngine()

    def start(self) -> None:
        if self.running:
            return
        self.capture = cv2.VideoCapture(self.camera_id)
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open camera {self.camera_id}")

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.capture:
            self.capture.release()

    def _run(self) -> None:
        pose = None
        if mp is not None:
            pose = mp.solutions.pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        while self.running and self.capture:
            ok, frame = self.capture.read()
            if not ok:
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)
            hand_near_hip = False
            hand_above_shoulder = False

            if pose is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = pose.process(rgb)
                if res.pose_landmarks:
                    lms = res.pose_landmarks.landmark
                    rw, lw = lms[16], lms[15]
                    rh, lh = lms[24], lms[23]
                    rs, ls = lms[12], lms[11]

                    hand_near_hip = (abs(rw.x - rh.x) < 0.08 and abs(rw.y - rh.y) < 0.12) or (
                        abs(lw.x - lh.x) < 0.08 and abs(lw.y - lh.y) < 0.12
                    )
                    hand_above_shoulder = rw.y < rs.y or lw.y < ls.y

            score, alert, reason = self.risk.update(hand_near_hip=hand_near_hip, hand_above_shoulder=hand_above_shoulder)

            color = (0, 0, 255) if alert else (0, 255, 0)
            cv2.putText(frame, f"risk={score} reason={reason}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            if alert:
                msg = {"ts": time.time(), "type": "alert", "score": score, "reason": reason}
                if not self.alert_queue.full():
                    self.alert_queue.put_nowait(msg)

            ok, encoded = cv2.imencode(".jpg", frame)
            if ok:
                self.latest_jpeg = encoded.tobytes()

            self.latest_state = {"score": score, "reason": reason, "alert": alert}
            time.sleep(0.01)

        if pose is not None:
            pose.close()
