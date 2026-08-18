import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# BASE PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

# Load local environment configuration when present.
# Secrets remain outside Git because .env is ignored.
load_dotenv(BASE_DIR / ".env", override=False)


# ============================================================
# RUNTIME / TENSORFLOW SETTINGS
# ============================================================

# Keep TensorFlow CPU-only and constrained on low-memory instances.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "1")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")


# ============================================================
# DATA PATHS
# ============================================================

DATA_DIR = BASE_DIR / "data"
KNOWN_FACES_DIR = DATA_DIR / "known_faces"
TEMP_DIR = DATA_DIR / "tmp"
EMBEDDING_INDEX_PATH = DATA_DIR / "face_embeddings.npz"


# ============================================================
# IMAGE / VIDEO QUALITY SETTINGS
# ============================================================

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", "5000000"))
QUALITY_BLUR_THRESHOLD = float(os.getenv("QUALITY_BLUR_THRESHOLD", "40"))
MIN_BRIGHTNESS = float(os.getenv("MIN_BRIGHTNESS", "35"))
MAX_BRIGHTNESS = float(os.getenv("MAX_BRIGHTNESS", "225"))


# ============================================================
# FACE EMBEDDING SETTINGS
# ============================================================

# Facenet512 is the validated project benchmark configuration.
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "Facenet512")

# Benchmark-selected operating threshold.
EMBEDDING_DISTANCE_THRESHOLD = float(
    os.getenv("EMBEDDING_DISTANCE_THRESHOLD", "0.375")
)


# ============================================================
# LIVENESS / ANTI-SPOOFING
# ============================================================

LIVENESS_ENABLED = os.getenv("LIVENESS_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


# ============================================================
# REQUIRED DIRECTORIES
# ============================================================

for path in (DATA_DIR, KNOWN_FACES_DIR, TEMP_DIR):
    path.mkdir(parents=True, exist_ok=True)
