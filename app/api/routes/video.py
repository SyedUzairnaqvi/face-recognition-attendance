import os
from pathlib import Path
from uuid import uuid4

import cv2
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import EMBEDDING_INDEX_PATH, TEMP_DIR
from app.models.face_recognizer import recognize_faces
from app.services.attendance_service import mark_attendance

router = APIRouter(prefix="/recognition", tags=["Recognition"])

MAX_VIDEO_UPLOAD_BYTES = int(os.getenv("MAX_VIDEO_UPLOAD_BYTES", "50000000"))
MAX_VIDEO_SECONDS = float(os.getenv("MAX_VIDEO_SECONDS", "120"))
VIDEO_SAMPLE_FPS = float(os.getenv("VIDEO_SAMPLE_FPS", "1"))


async def _save_upload(upload: UploadFile, destination: Path) -> int:
    total = 0
    with destination.open("wb") as output:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_VIDEO_UPLOAD_BYTES:
                output.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"Video is too large. Maximum size is {MAX_VIDEO_UPLOAD_BYTES // 1_000_000} MB.",
                )
            output.write(chunk)
    return total


@router.post("/video")
async def verify_video(file: UploadFile = File(...)):
    """Scan a video for registered faces and mark each matched person once."""
    content_type = (file.content_type or "").lower()
    allowed_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    suffix = Path(file.filename or "").suffix.lower()

    if not content_type.startswith("video/") and suffix not in allowed_extensions:
        raise HTTPException(status_code=415, detail="Upload a video file (MP4, MOV, AVI, MKV, or WEBM)")

    if not EMBEDDING_INDEX_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Embedding index is not ready. Register at least one face first.",
        )

    video_path = TEMP_DIR / f"{uuid4().hex}{suffix or '.mp4'}"
    await _save_upload(file, video_path)

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        video_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Could not open the uploaded video")

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps > 0 else 0

    if duration > MAX_VIDEO_SECONDS:
        capture.release()
        video_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=413,
            detail=f"Video is too long. Maximum duration is {int(MAX_VIDEO_SECONDS)} seconds.",
        )

    sample_every = max(1, int(round(fps / max(VIDEO_SAMPLE_FPS, 0.1)))) if fps > 0 else 1
    frame_index = 0
    sampled_frames = 0
    faces_detected = 0
    unknown_faces = 0
    recognized_people = {}

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            if frame_index % sample_every != 0:
                frame_index += 1
                continue

            sampled_frames += 1
            frame_path = TEMP_DIR / f"{uuid4().hex}.jpg"
            try:
                if not cv2.imwrite(str(frame_path), frame):
                    continue

                results = recognize_faces(str(frame_path), None)
                faces_detected += len(results)

                for result in results:
                    if not result.get("matched"):
                        unknown_faces += 1
                        continue

                    name = str(result["name"])
                    if name in recognized_people:
                        continue

                    attendance = mark_attendance(
                        name,
                        result.get("distance"),
                        result.get("threshold"),
                        None,
                        None,
                    )
                    recognized_people[name] = {
                        "name": name,
                        "match_score": result.get("match_score"),
                        "distance": result.get("distance"),
                        "threshold": result.get("threshold"),
                        "attendance": attendance,
                    }
            finally:
                frame_path.unlink(missing_ok=True)

            frame_index += 1
    finally:
        capture.release()
        video_path.unlink(missing_ok=True)

    return {
        "status": "processed",
        "video": {
            "filename": file.filename,
            "duration_seconds": round(duration, 2),
            "sampled_frames": sampled_frames,
            "faces_detected": faces_detected,
        },
        "recognized": list(recognized_people.values()),
        "unknown_faces": unknown_faces,
        "attendance": [item["attendance"] for item in recognized_people.values()],
    }
