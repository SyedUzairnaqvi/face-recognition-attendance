import re
from uuid import uuid4

import cv2
from deepface import DeepFace
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import (
    EMBEDDING_INDEX_PATH,
    KNOWN_FACES_DIR,
    LIVENESS_ENABLED,
    MAX_UPLOAD_BYTES,
)
from app.models.embedding_engine import build_embedding_index
from app.services.liveness_service import assess_liveness
from app.services.quality_service import assess_image

router = APIRouter(prefix="/enrollment", tags=["Enrollment"])


@router.post("/register")
async def register(name: str, file: UploadFile = File(...)):
    """Register one person from a face image and rebuild the embedding index."""
    clean_name = re.sub(r"[^A-Za-z0-9 _-]", "", name).strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="A valid name is required")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Upload an image file")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large")

    temp_path = KNOWN_FACES_DIR / f".{uuid4().hex}.jpg"
    person_dir = KNOWN_FACES_DIR / clean_name
    person_dir.mkdir(parents=True, exist_ok=True)
    image_path = person_dir / f"{uuid4().hex}.jpg"
    temp_path.write_bytes(data)

    try:
        image = cv2.imread(str(temp_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image")

        quality = assess_image(image)
        if not quality["accepted"]:
            raise HTTPException(status_code=400, detail={"reason": "image_quality", "quality": quality})

        # Use RetinaFace instead of OpenCV Haar Cascade on Render.
        faces = DeepFace.extract_faces(
            img_path=str(temp_path),
            detector_backend="retinaface",
            enforce_detection=True,
            align=True,
            anti_spoofing=LIVENESS_ENABLED,
        )

        if len(faces) != 1:
            raise HTTPException(status_code=400, detail="Enrollment image must contain exactly one face")

        liveness = assess_liveness(faces[0])
        if LIVENESS_ENABLED and not liveness["is_real"]:
            raise HTTPException(status_code=400, detail={"reason": "spoof_detected", "liveness": liveness})

        temp_path.replace(image_path)

        try:
            result = build_embedding_index(KNOWN_FACES_DIR)
        except Exception:
            image_path.unlink(missing_ok=True)
            raise

        return {
            "status": "registered",
            "name": clean_name,
            "quality": quality,
            "liveness": liveness,
            "embedding_index": result,
            "note": "Registration data is stored on the service filesystem. Configure persistent storage before relying on it across Render restarts/deploys.",
        }
    finally:
        temp_path.unlink(missing_ok=True)
