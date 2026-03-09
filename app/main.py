from __future__ import annotations

import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse

from app.camera import CameraWorker

app = FastAPI(title="Retail Theft Detection Demo")
camera = CameraWorker(camera_id=0)


@app.on_event("startup")
def startup_event() -> None:
    camera.start()


@app.on_event("shutdown")
def shutdown_event() -> None:
    camera.stop()


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "camera_running": camera.running, "state": camera.latest_state})


@app.get("/video_feed")
def video_feed() -> StreamingResponse:
    def gen():
        while True:
            if camera.latest_jpeg is None:
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + camera.latest_jpeg + b"\r\n"
            )

    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            try:
                msg = await asyncio.wait_for(camera.alert_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                msg = {"type": "heartbeat", **camera.latest_state}
            await websocket.send_json(msg)
    except Exception:
        await websocket.close()
