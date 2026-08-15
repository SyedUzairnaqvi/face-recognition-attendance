import re
from uuid import uuid4

import cv2
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.core.config import KNOWN_FACES_DIR, MAX_UPLOAD_BYTES
from app.models.embedding_engine import build_embedding_index
from app.services.quality_service import assess_image

router = APIRouter(prefix="/enrollment", tags=["Enrollment"])

_build_state = {
    "status": "idle",
    "result": None,
    "error": None,
}


def _run_build_index():
    global _build_state

    _build_state = {
        "status": "building",
        "result": None,
        "error": None,
    }

    try:
        result = build_embedding_index(KNOWN_FACES_DIR)
        _build_state = {
            "status": "ready",
            "result": result,
            "error": None,
        }
        print(f"Embedding index built successfully: {result}")
    except Exception as exc:
        _build_state = {
            "status": "failed",
            "result": None,
            "error": str(exc),
        }
        print(f"Embedding index build failed: {exc}")


@router.post("/register")
async def register(
    name: str,
    file: UploadFile = File(...),
):
    """Register an image without running heavy DeepFace work in the HTTP request."""
    clean_name = re.sub(r"[^A-Za-z0-9 _-]", "", name).strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="A valid name is required")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Upload an image file")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large")

    temp_path = KNOWN_FACES_DIR / f".{uuid4().hex}.tmp"
    temp_path.write_bytes(data)
    image = cv2.imread(str(temp_path))
    temp_path.unlink(missing_ok=True)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    quality = assess_image(image)
    if not quality["accepted"]:
        raise HTTPException(
            status_code=400,
            detail={"reason": "image_quality", "quality": quality},
        )

    person_dir = KNOWN_FACES_DIR / clean_name
    person_dir.mkdir(parents=True, exist_ok=True)
    image_path = person_dir / f"{uuid4().hex}.jpg"
    image_path.write_bytes(data)

    return {
        "status": "registered",
        "name": clean_name,
        "image_saved": True,
        "image_path": str(image_path),
        "quality": quality,
        "embedding_build": "pending",
        "note": "Image registered successfully. Call /enrollment/build-index before recognition.",
    }


@router.post("/build-index", status_code=202)
def build_index(background_tasks: BackgroundTasks):
    """Start the face embedding index build in the background."""
    if _build_state["status"] == "building":
        return {
            "status": "building",
            "message": "Embedding index build is already running.",
        }

    background_tasks.add_task(_run_build_index)

    return {
        "status": "building",
        "message": "Embedding index build started. Poll /enrollment/build-index/status.",
    }


@router.get("/build-index/status")
def build_index_status():
    """Return the current embedding index build status."""
    return _build_state
