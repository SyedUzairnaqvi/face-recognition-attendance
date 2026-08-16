import cv2
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import TEMP_DIR, MAX_UPLOAD_BYTES, EMBEDDING_INDEX_PATH
from app.models.face_recognizer import recognize_faces
from app.services.attendance_service import mark_attendance
from app.services.quality_service import assess_image

router = APIRouter(prefix="/recognition", tags=["Recognition"])


@router.post("/verify")
async def verify(file: UploadFile = File(...)):
    """Verify a face and mark attendance when a configured identity matches."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Upload an image file")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large")

    temp_path = TEMP_DIR / f"{uuid4().hex}.jpg"
    temp_path.write_bytes(data)

    try:
        image = cv2.imread(str(temp_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image")

        quality = assess_image(image)
        if not quality["accepted"]:
            return {
                "status": "rejected",
                "reason": "image_quality",
                "quality": quality,
                "recognitions": [],
                "attendance": [],
            }

        if not EMBEDDING_INDEX_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail="Embedding index is not ready. Register a face and run /enrollment/build-index.",
            )

        try:
            results = recognize_faces(str(temp_path), None)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            # Model/index/configuration failures should be diagnosable instead of a generic 500.
            raise HTTPException(
                status_code=503,
                detail=f"Recognition service is not ready: {exc}",
            ) from exc
        except Exception as exc:
            # Keep unexpected CV/DeepFace failures from leaking an opaque server 500.
            print(f"Recognition failure: {type(exc).__name__}: {exc}")
            raise HTTPException(
                status_code=503,
                detail="Recognition model failed to process the image. Check Render logs and retry after the model is loaded.",
            ) from exc

        if not results:
            return {
                "status": "rejected",
                "reason": "no_face_detected",
                "quality": quality,
                "recognitions": [],
                "attendance": [],
            }

        attendance = []
        for result in results:
            if result["matched"]:
                attendance.append(
                    mark_attendance(
                        result["name"],
                        result["distance"],
                        result["threshold"],
                        quality["blur_score"],
                        quality["brightness"],
                    )
                )

        return {
            "status": "processed",
            "quality": quality,
            "recognitions": results,
            "attendance": attendance,
        }
    finally:
        temp_path.unlink(missing_ok=True)
