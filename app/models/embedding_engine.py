from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np

try:
    from deepface import DeepFace as _DeepFace
except ImportError:  # Keep API startup/test collection usable without ML extras.
    _DeepFace = None


class _DeepFaceProxy:
    def _require(self):
        if _DeepFace is None:
            raise RuntimeError(
                "DeepFace is not installed. Install requirements.txt to enable face recognition."
            )
        return _DeepFace

    def represent(self, *args, **kwargs):
        return self._require().represent(*args, **kwargs)

    def extract_faces(self, *args, **kwargs):
        return self._require().extract_faces(*args, **kwargs)


DeepFace = _DeepFaceProxy()

from app.core.config import (
    EMBEDDING_INDEX_PATH,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_DISTANCE_THRESHOLD,
    KNOWN_FACES_DIR,
    LIVENESS_ENABLED,
)
from app.services.liveness_service import assess_liveness

_FACE_CASCADE = cv2.CascadeClassifier(
    str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml")
)


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 1.0
    return float(1.0 - np.dot(a, b) / denom)


def _detect_faces(image: np.ndarray) -> list[dict]:
    if image is None or image.size == 0:
        return []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    boxes = _FACE_CASCADE.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )
    return [
        {
            "face": image[y:y + h, x:x + w],
            "facial_area": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
        }
        for x, y, w, h in boxes
    ]


def _embedding_from_face(face: np.ndarray) -> np.ndarray | None:
    if face is None or face.size == 0:
        return None
    representations = DeepFace.represent(
        img_path=face,
        model_name=EMBEDDING_MODEL_NAME,
        detector_backend="skip",
        enforce_detection=False,
    )
    if not representations:
        return None
    embedding = np.asarray(representations[0]["embedding"], dtype=np.float32)
    embedding /= max(np.linalg.norm(embedding), 1e-12)
    return embedding


def _extract_live_faces(image) -> list[dict]:
    """Compatibility/testable wrapper around DeepFace anti-spoof extraction."""
    try:
        return DeepFace.extract_faces(
            img_path=image,
            detector_backend="opencv",
            enforce_detection=False,
            align=True,
            anti_spoofing=True,
        )
    except Exception:
        return []


def _check_liveness(face: np.ndarray) -> dict:
    """Run DeepFace anti-spoofing and normalize the result.

    Liveness is fail-closed: when enabled, an unavailable anti-spoofing
    result must never be allowed to create attendance.
    """
    if not LIVENESS_ENABLED:
        return assess_liveness({})

    try:
        faces = DeepFace.extract_faces(
            img_path=face,
            detector_backend="opencv",
            enforce_detection=False,
            align=True,
            anti_spoofing=True,
        )
    except Exception as exc:
        print(f"Liveness check failed: {type(exc).__name__}: {exc}")
        return {
            "enabled": True,
            "is_real": False,
            "score": None,
            "status": "unavailable",
        }

    if not faces:
        return {
            "enabled": True,
            "is_real": False,
            "score": None,
            "status": "unavailable",
        }

    face_obj = max(
        faces,
        key=lambda item: (
            item.get("facial_area", {}).get("w", 0)
            * item.get("facial_area", {}).get("h", 0)
        ),
    )
    return assess_liveness(face_obj)


def build_embedding_index(known_faces_dir: Path) -> dict:
    embeddings: List[np.ndarray] = []
    names: List[str] = []
    sources: List[str] = []

    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    files = sorted(
        p for p in known_faces_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in image_extensions
    )
    if not files:
        raise ValueError(f"No face images found under {known_faces_dir}")

    for image_path in files:
        relative_parts = image_path.relative_to(known_faces_dir).parts
        name = relative_parts[0] if len(relative_parts) > 1 else image_path.stem
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"Skipping invalid image: {image_path}")
            continue

        faces = _detect_faces(image)
        if not faces:
            print(f"Skipping {image_path}: no face detected")
            continue

        face_obj = max(
            faces,
            key=lambda item: item["facial_area"]["w"] * item["facial_area"]["h"],
        )
        try:
            embedding = _embedding_from_face(face_obj["face"])
        except Exception as exc:
            print(f"Skipping {image_path}: {exc}")
            continue
        if embedding is None:
            continue

        embeddings.append(embedding)
        names.append(name)
        sources.append(str(image_path))

    if not embeddings:
        raise RuntimeError("No usable face embeddings were generated.")

    matrix = np.vstack(embeddings).astype(np.float32)
    # Write to a temporary file in the same directory, then atomically replace
    # the live index. Readers therefore never observe a half-written NPZ file.
    EMBEDDING_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = EMBEDDING_INDEX_PATH.with_suffix(".tmp.npz")
    np.savez_compressed(
        temp_path,
        embeddings=matrix,
        names=np.asarray(names),
        sources=np.asarray(sources),
        model=np.asarray([EMBEDDING_MODEL_NAME]),
    )
    temp_path.replace(EMBEDDING_INDEX_PATH)
    return {
        "index_path": str(EMBEDDING_INDEX_PATH),
        "model": EMBEDDING_MODEL_NAME,
        "embedding_count": int(len(names)),
        "people": int(len(set(names))),
    }


def load_embedding_index() -> Dict[str, np.ndarray]:
    if not EMBEDDING_INDEX_PATH.exists():
        return build_and_load_index()

    try:
        with np.load(EMBEDDING_INDEX_PATH, allow_pickle=False) as data:
            model = str(data["model"][0])
            if model == EMBEDDING_MODEL_NAME:
                return {
                    "embeddings": data["embeddings"].astype(np.float32),
                    "names": data["names"].astype(str),
                    "sources": data["sources"].astype(str),
                }
            print(
                f"Stale embedding index detected: {model}; "
                f"configured model is {EMBEDDING_MODEL_NAME}. Rebuilding."
            )
    except Exception as exc:
        print(f"Embedding index could not be loaded cleanly: {exc}. Rebuilding.")

    return build_and_load_index()


def build_and_load_index() -> Dict[str, np.ndarray]:
    """Rebuild the index from current enrollment images, then load it."""
    build_embedding_index(KNOWN_FACES_DIR)
    with np.load(EMBEDDING_INDEX_PATH, allow_pickle=False) as data:
        model = str(data["model"][0])
        if model != EMBEDDING_MODEL_NAME:
            raise RuntimeError(
                f"Index rebuild produced {model}, but application is configured for {EMBEDDING_MODEL_NAME}."
            )
        embeddings = data["embeddings"].astype(np.float32)
        names = data["names"].astype(str)
        sources = data["sources"].astype(str)
    return {"embeddings": embeddings, "names": names, "sources": sources}


def recognize_with_embeddings(img_path: str) -> List[dict]:
    index = load_embedding_index()
    image = cv2.imread(str(img_path))
    face_objects = _detect_faces(image)
    results: List[dict] = []

    for face_obj in face_objects:
        facial_area = face_obj.get("facial_area", {})
        face = face_obj["face"]

        liveness = _check_liveness(face)
        if LIVENESS_ENABLED and liveness.get("is_real") is not True:
            results.append({
                "name": "Unknown",
                "matched": False,
                "distance": None,
                "threshold": EMBEDDING_DISTANCE_THRESHOLD,
                "match_score": 0,
                "engine": "embedding_cosine",
                "model": EMBEDDING_MODEL_NAME,
                "liveness": liveness,
                "face_box": facial_area,
                "reason": "liveness_failed",
            })
            continue

        try:
            query = _embedding_from_face(face)
        except Exception as exc:
            print(f"Embedding failed: {exc}")
            query = None

        if query is None:
            results.append({
                "name": "Unknown",
                "matched": False,
                "distance": None,
                "threshold": EMBEDDING_DISTANCE_THRESHOLD,
                "match_score": 0,
                "engine": "embedding_cosine",
                "model": EMBEDDING_MODEL_NAME,
                "liveness": liveness,
                "face_box": facial_area,
                "reason": "embedding_failed",
            })
            continue

        distances = np.array(
            [_cosine_distance(query, row) for row in index["embeddings"]]
        )
        best_idx = int(np.argmin(distances))
        distance = float(distances[best_idx])
        matched = distance <= EMBEDDING_DISTANCE_THRESHOLD
        name = str(index["names"][best_idx]) if matched else "Unknown"
        score = max(
            0.0,
            min(
                100.0,
                (1.0 - distance / EMBEDDING_DISTANCE_THRESHOLD) * 100.0,
            ),
        )

        results.append({
            "name": name,
            "matched": matched,
            "distance": round(distance, 6),
            "threshold": EMBEDDING_DISTANCE_THRESHOLD,
            "match_score": round(score, 2),
            "engine": "embedding_cosine",
            "model": EMBEDDING_MODEL_NAME,
            "liveness": liveness,
            "face_box": facial_area,
        })

    return results
