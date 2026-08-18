import threading

import numpy as np

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import init_db

from app.api.routes import (
    recognition,
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

from app.models.embedding_engine import build_embedding_index


# ============================================================
# DATABASE STARTUP
# ============================================================

ensure_seed_faces(KNOWN_FACES_DIR)

# The experiment branch must remain bootable when Render has no
# remote MySQL. The production/local main branch is unchanged.
try:
    init_db()
except Exception as exc:
    print(
        "Database startup check skipped on analytics experiment: "
        f"{type(exc).__name__}: {exc}"
    )


# ============================================================
# EMBEDDING INDEX CHECK
# ============================================================

def _index_is_compatible():

    if not EMBEDDING_INDEX_PATH.exists():
        return False

    try:

        with np.load(
            EMBEDDING_INDEX_PATH,
            allow_pickle=False,
        ) as data:

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
# AUTOMATIC INDEX BUILD
# ============================================================

def _auto_build_index():

    try:

        result = build_embedding_index(KNOWN_FACES_DIR)

        print(f"Automatic embedding index build completed: {result}")

    except Exception as exc:

        print(
            "Automatic embedding index build failed: "
            f"{type(exc).__name__}: {exc}"
        )


if not _index_is_compatible():

    threading.Thread(
        target=_auto_build_index,
        daemon=True,
        name="embedding-index-build",
    ).start()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Secure Vision Attendance API",
    version="2.1.0",
    description=(
        "Computer-vision identity verification, video attendance, "
        "quality checks, and duplicate-safe attendance API."
    ),
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(health.router)
app.include_router(recognition.router)
app.include_router(attendance.router)
app.include_router(enrollment.router)
app.include_router(video.router)

# Safe public analytics endpoint. It does not touch MySQL.
app.include_router(analytics_public_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def home():

    return {
        "message": "Secure Vision Attendance API is running",
        "docs": "/docs",
    }
