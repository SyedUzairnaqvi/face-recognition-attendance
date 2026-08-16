import os
from pathlib import Path

# Keep TensorFlow CPU-only and constrained on low-memory Render instances.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "1")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
KNOWN_FACES_DIR = DATA_DIR / "known_faces"
DB_PATH = DATA_DIR / "attendance.db"
TEMP_DIR = DATA_DIR / "tmp"
EMBEDDING_INDEX_PATH = DATA_DIR / "face_embeddings.npz"

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD