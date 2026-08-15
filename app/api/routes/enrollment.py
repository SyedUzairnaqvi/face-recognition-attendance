import re
from uuid import uuid4

import cv2
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import KNOWN_FACES_DIR, MAX_UPLOAD_BYTES
from app.services.quality_service import assess_image

router = APIRouter(prefix="/enrollment", tags=["Enrollment"])


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

    # Heavy DeepFace embedding generation is intentionally not run here.
    # This keeps enrollment reliable on Render's free 512 MB instance.
    return {
        "status": "registered",
        "name": clean_name,
        "image_saved": True,
        "image_path": str(image_path),
        "quality": quality,
        "embedding_build": "pending",
        "note": "Image registered successfully. Build the embedding index before recognition.",
    }
