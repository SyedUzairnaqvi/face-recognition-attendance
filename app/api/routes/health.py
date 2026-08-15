from fastapi import APIRouter
from app.core.config import KNOWN_FACES_DIR, EMBEDDING_INDEX_PATH, EMBEDDING_MODEL_NAME

router = APIRouter(tags=["System"])


@router.get("/health")
def health():
    face_files = [
        p for p in KNOWN_FACES_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ]
    return {
        "status": "ok",
        "known_faces_directory": KNOWN_FACES_DIR.exists(),
        "known_face_files": len(face_files),
        "embedding_index_ready": EMBEDDING_INDEX_PATH.exists(),
        "embedding_model": EMBEDDING_MODEL_NAME,
    }
