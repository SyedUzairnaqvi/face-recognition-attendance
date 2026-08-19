import threading
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    recognition,
    recognition_batch,
    attendance,
    health,
    enrollment,
    video,
)
from app.api.routes.analytics_public import router as analytics_public_router
from app.core.config import (
    KNOWN_FACES_DIR,
    EMBEDDING_INDEX_PATH,
    EMBEDDING_MODEL_NAME,
)
from app.core.seed_faces import ensure_seed_faces
from app.db.database import init_db


def _index_is_compatible() -> bool:
    if not EMBEDDING_INDEX_PATH.exists():
        return False

    try:
        with np.load(EMBEDDING_INDEX_PATH, allow_pickle=False) as data:
            model = str(data["model"][0])
            embeddings = data["embeddings"]
            names = data["names"]
            return (
                model == EMBEDDING_MODEL_NAME
                and embeddings.ndim == 2
                and embeddings.shape[0] > 0
                and len(embeddings) == len(names)
            )
    except Exception:
        return False


def _auto_build_index() -> None:
    try:
        # Lazy import keeps basic API/health startup independent of the heavy
        # DeepFace/TensorFlow stack until recognition is actually needed.
        from app.models.embedding_engine import build_embedding_index

        result = build_embedding_index(KNOWN_FACES_DIR)
        print(f"Automatic embedding index build completed: {result}")
    except Exception as exc:
        print(f"Automatic embedding index build failed: {type(exc).__name__}: {exc}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize optional resources at ASGI startup, never at import time."""
    ensure_seed_faces(KNOWN_FACES_DIR)

    try:
        init_db()
        print("MySQL schema/connectivity check passed.")
    except Exception as exc:
        # The service remains available for /health and non-DB routes.
        print(f"MySQL startup check failed: {type(exc).__name__}: {exc}")

    if not _index_is_compatible():
        threading.Thread(
            target=_auto_build_index,
            daemon=True,
            name="embedding-index-build",
        ).start()

    yield


app = FastAPI(
    title="Secure Vision Attendance API",
    version="2.3.0",
    description=(
        "Computer-vision identity verification, high-volume batch recognition, "
        "video attendance, quality checks, analytics, and duplicate-safe attendance API."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(recognition.router)
app.include_router(recognition_batch.router)
app.include_router(attendance.router)
app.include_router(enrollment.router)
app.include_router(video.router)
app.include_router(analytics_public_router)


@app.get("/")
def home():
    return {
        "message": "Secure Vision Attendance API is running",
        "docs": "/docs",
        "health": "/health",
        "batch_recognition": "/recognition/batch-verify",
    }
