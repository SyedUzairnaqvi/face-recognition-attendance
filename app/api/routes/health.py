import numpy as np
from fastapi import APIRouter

from app.core.config import (
    KNOWN_FACES_DIR,
    EMBEDDING_INDEX_PATH,
    EMBEDDING_MODEL_NAME,
)

router = APIRouter(tags=["System"])


@router.get("/health")
def health():
    """Return service health separately from embedding-index readiness."""

    face_files = [
        p
        for p in KNOWN_FACES_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ]

    index_ready = False
    index_model = None
    index_error = None

    if EMBEDDING_INDEX_PATH.exists():
        try:
            with np.load(EMBEDDING_INDEX_PATH, allow_pickle=False) as data:
                index_model = str(data["model"][0])
                embeddings = data["embeddings"]
                names = data["names"]

                index_ready = (
                    index_model == EMBEDDING_MODEL_NAME
                    and embeddings.ndim == 2
                    and len(embeddings) == len(names)
                    and len(names) > 0
                )

                if not index_ready:
                    index_error = (
                        "Embedding index is incompatible with the configured "
                        "model or is empty."
                    )
        except Exception as exc:
            index_error = f"Embedding index could not be loaded: {exc}"

    return {
        # The API process itself is healthy even while the embedding index
        # is being built asynchronously during startup.
        "status": "ok",
        "service": "online",
        "known_faces_directory": KNOWN_FACES_DIR.exists(),
        "known_face_files": len(face_files),
        "embedding_index_ready": index_ready,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "index_model": index_model,
        "index_error": index_error,
    }
