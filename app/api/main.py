import threading
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db
from app.api.routes import recognition, attendance, health, enrollment
from app.core.config import (
    KNOWN_FACES_DIR,
    EMBEDDING_INDEX_PATH,
    EMBEDDING_MODEL_NAME,
)
from app.core.seed_faces import ensure_seed_faces
from app.models.embedding_engine import build_embedding_index


# ============================================================
# STARTUP SETUP
# ============================================================

# Render Free has an ephemeral filesystem,
# so restore the demo enrollment image on startup.
ensure_seed_faces(KNOWN_FACES_DIR)

# Initialize the attendance database.
init_db()


# ============================================================
# EMBEDDING INDEX COMPATIBILITY CHECK
# ============================================================

def _index_is_compatible() -> bool:
    """
    Check whether the existing embedding index:
    1. Exists
    2. Uses the currently configured model
    3. Contains valid embeddings
    4. Has matching names and embeddings
    """

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
                and len(embeddings) > 0
                and len(embeddings) == len(names)
            )

    except Exception:
        return False


# ============================================================
# AUTOMATIC EMBEDDING INDEX BUILD
# ============================================================

def _auto_build_index() -> None:
    """
    Automatically rebuild the embedding index when:
    - the index does not exist
    - the index uses a different model
    - the index is invalid
    """

    try:
        result = build_embedding_index(KNOWN_FACES_DIR)

        print(
            f"Automatic embedding index build completed: {result}"
        )

    except Exception as exc:

        print(
            f"Automatic embedding index build failed: "
            f"{type(exc).__name__}: {exc}"
        )


# Rebuild automatically when Render has a stale/missing index
# after a deployment or model change.
#
# This removes the need to manually rebuild embeddings
# whenever the configured embedding model changes.
if not _index_is_compatible():

    threading.Thread(
        target=_auto_build_index,
        daemon=True,
        name="embedding-index-build",
    ).start()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Secure Vision Attendance API",
    version="2.0.0",
    description=(
        "Computer-vision identity verification and attendance API "
        "with quality checks and duplicate prevention."
    ),
)


# ============================================================
# CORS
# ============================================================

# Allow the separate frontend to communicate with this API
# from a browser.
#
# This is required because the frontend and Render API
# may run on different origins.
app.add_middleware(
    CORSMiddleware,

    # Allow requests from the frontend.
    allow_origins=["*"],

    # We are not using cookies/auth credentials here.
    allow_credentials=False,

    # Allow GET, POST, OPTIONS, etc.
    allow_methods=["*"],

    # Allow Content-Type, Accept, etc.
    allow_headers=["*"],
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(health.router)

app.include_router(recognition.router)

app.include_router(attendance.router)

app.include_router(enrollment.router)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Secure Vision Attendance API is running",
        "docs": "/docs",
    }