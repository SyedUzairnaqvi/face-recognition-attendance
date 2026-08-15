import re
from uuid import uuid4

import cv2
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.core.config import KNOWN_FACES_DIR, MAX_UPLOAD_BYTES
from app.models.embedding_engine import build_embedding_index
from app.services.quality_service import assess_image

router = APIRouter(prefix="/enrollment", tags=["Enrollment"])


def _rebuild_embeddings() -> None:
    """Build embeddings after the HTTP response so Render does not time out."""
    try:
        result = build_embedding_index(KNOWN_FACES_DIR)
        print(f"Enrollment embedding rebuild complete: {result}")
    except Exception as exc:
        # Keep the API request successful; the image remains stored and can be rebuilt later.
        print(f"Enrollment embedding rebuild failed: {exc}")


@router.post("/register")
async def register(
    name: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Register one person quickly; rebuild embeddings in the background."""
    clean_name = re.sub(r"[^A-Za-z0-9 _-]", "", name).strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="A valid name is required")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Upload an image file")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large")

    # Check that the uploaded bytes are actually a readable image.
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

    # Store the original upload under the person's name.
    person_dir = KNOWN_FACES_DIR / clean_name
    person_dir.mkdir(parents=True, exist_ok=True)
    image_path = person_dir / f"{uuid4().hex}.jpg"
    image_path.write_bytes(data)

    # IMPORTANT: DeepFace/RetinaFace/Facenet512 can take a long time on Render.
    # Do not make the browser wait for the embedding rebuild.
    background_tasks.add_task(_rebuild_embeddings)

    return {
        "status": "registered",
        "name": clean_name,
        "image_saved": True,
        "image_path": str(image_path),
        "quality": quality,
        "embedding_build": "started_in_background",
        "note": "Wait a little before calling recognition. Render filesystem storage is temporary unless persistent storage is configured.",
    }
