import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
KNOWN_FACES_DIR = DATA_DIR / "known_faces"
DB_PATH = DATA_DIR / "attendance.db"
TEMP_DIR = DATA_DIR / "tmp"
EMBEDDING_INDEX_PATH = DATA_DIR / "face_embeddings.npz"

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", "5000000"))
QUALITY_BLUR_THRESHOLD = float(os.getenv("QUALITY_BLUR_THRESHOLD", "40"))
MIN_BRIGHTNESS = float(os.getenv("MIN_BRIGHTNESS", "35"))
MAX_BRIGHTNESS = float(os.getenv("MAX_BRIGHTNESS", "225"))
# FaceNet is substantially lighter than FaceNet512 and is a better fit for Render Free.
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "Facenet")
EMBEDDING_DISTANCE_THRESHOLD = float(os.getenv("EMBEDDING_DISTANCE_THRESHOLD", "0.30"))
LIVENESS_ENABLED = os.getenv("LIVENESS_ENABLED", "false").lower() in {"1", "true", "yes", "on"}

for p in (DATA_DIR, KNOWN_FACES_DIR, TEMP_DIR):
    p.mkdir(parents=True, exist_ok=True)
