from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

import cv2
import numpy as np

from app.core.config import (
    EMBEDDING_DISTANCE_THRESHOLD,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_INDEX_PATH,
    LIVENESS_ENABLED,
)
from app.db.database import get_connection
from app.models.embedding_engine import _detect_faces, _embedding_from_face, load_embedding_index


IST = timezone(timedelta(hours=5, minutes=30))

_INDEX_CACHE: dict | None = None
_INDEX_MTIME_NS: int | None = None


def _get_cached_index() -> dict:
    global _INDEX_CACHE, _INDEX_MTIME_NS

    if not EMBEDDING_INDEX_PATH.exists():
        raise FileNotFoundError("Embedding index is not ready.")

    mtime_ns = EMBEDDING_INDEX_PATH.stat().st_mtime_ns
    if _INDEX_CACHE is None or _INDEX_MTIME_NS != mtime_ns:
        index = load_embedding_index()
        matrix = np.asarray(index["embeddings"], dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        matrix = matrix / np.maximum(norms, 1e-12)
        _INDEX_CACHE = {
            "embeddings": matrix,
            "names": np.asarray(index["names"], dtype=str),
        }
        _INDEX_MTIME_NS = mtime_ns

    return _INDEX_CACHE


def recognize_image_bytes(data: bytes) -> list[dict]:
    """Fast in-memory recognition with cached/vectorized matching.

    Liveness is never bypassed. If it is enabled, batch image recognition
    returns a non-match instead of weakening the security model.
    """
    image_array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Invalid image")

    index = _get_cached_index()
    face_objects = _detect_faces(image)
    results: list[dict] = []

    for face_obj in face_objects:
        facial_area = face_obj.get("facial_area", {})

        if LIVENESS_ENABLED:
            results.append({
                "name": "Unknown",
                "matched": False,
                "distance": None,
                "threshold": EMBEDDING_DISTANCE_THRESHOLD,
                "match_score": 0,
                "engine": "embedding_cosine_vectorized",
                "model": EMBEDDING_MODEL_NAME,
                "face_box": facial_area,
                "reason": "liveness_requires_interactive_verification",
            })
            continue

        query = _embedding_from_face(face_obj["face"])
        if query is None:
            results.append({
                "name": "Unknown",
                "matched": False,
                "distance": None,
                "threshold": EMBEDDING_DISTANCE_THRESHOLD,
                "match_score": 0,
                "engine": "embedding_cosine_vectorized",
                "model": EMBEDDING_MODEL_NAME,
                "face_box": facial_area,
                "reason": "embedding_failed",
            })
            continue

        distances = 1.0 - np.dot(index["embeddings"], query)
        best_idx = int(np.argmin(distances))
        distance = float(distances[best_idx])
        matched = distance <= EMBEDDING_DISTANCE_THRESHOLD
        name = str(index["names"][best_idx]) if matched else "Unknown"
        score = max(
            0.0,
            min(100.0, (1.0 - distance / EMBEDDING_DISTANCE_THRESHOLD) * 100.0),
        )

        results.append({
            "name": name,
            "matched": matched,
            "distance": round(distance, 6),
            "threshold": EMBEDDING_DISTANCE_THRESHOLD,
            "match_score": round(score, 2),
            "engine": "embedding_cosine_vectorized",
            "model": EMBEDDING_MODEL_NAME,
            "face_box": facial_area,
        })

    return results


def bulk_store_results(results: Iterable[dict], source: str = "Batch Image Recognition") -> dict:
    """Persist a batch with one MySQL transaction and bulk inserts."""
    rows = list(results)
    now = datetime.now(IST)
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    matched_names = sorted({
        str(row["name"])
        for row in rows
        if row.get("matched") and row.get("name")
    })

    attendance_status: dict[str, str] = {}
    person_ids: dict[str, int] = {}

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        if matched_names:
            placeholders = ",".join(["%s"] * len(matched_names))
            cursor.execute(
                f"SELECT person_id, name FROM persons WHERE name IN ({placeholders})",
                tuple(matched_names),
            )
            for person in cursor.fetchall():
                person_ids[str(person["name"])] = int(person["person_id"])

            missing = [name for name in matched_names if name not in person_ids]
            if missing:
                cursor.executemany(
                    "INSERT INTO persons (name) VALUES (%s)",
                    [(name,) for name in missing],
                )
                cursor.execute(
                    f"SELECT person_id, name FROM persons WHERE name IN ({placeholders})",
                    tuple(matched_names),
                )
                for person in cursor.fetchall():
                    person_ids[str(person["name"])] = int(person["person_id"])

            ids = [person_ids[name] for name in matched_names]
            id_placeholders = ",".join(["%s"] * len(ids))
            cursor.execute(
                f"SELECT person_id FROM attendance WHERE attendance_date=%s AND person_id IN ({id_placeholders})",
                (today, *ids),
            )
            existing = {int(row["person_id"]) for row in cursor.fetchall()}

            cursor.executemany(
                """
                INSERT IGNORE INTO attendance
                (person_id, attendance_date, attendance_time, status, method)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [
                    (person_ids[name], today, current_time, "Present", "Batch Face Recognition")
                    for name in matched_names
                ],
            )

            for name in matched_names:
                attendance_status[name] = (
                    "already_marked_today"
                    if person_ids[name] in existing
                    else "marked"
                )

        event_rows = []
        for row in rows:
            name = row.get("name") if row.get("matched") else None
            event_rows.append(
                (
                    person_ids.get(str(name)) if name else None,
                    "matched" if row.get("matched") else "unknown",
                    row.get("match_score"),
                    row.get("distance"),
                    row.get("threshold"),
                    source,
                    None,
                )
            )

        if event_rows:
            cursor.executemany(
                """
                INSERT INTO recognition_events
                (person_id, result, match_score, distance, threshold, source, video_filename)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                event_rows,
            )

        cursor.close()

    return {
        "saved_events": len(event_rows),
        "matched_faces": sum(1 for row in rows if row.get("matched")),
        "unknown_faces": sum(1 for row in rows if not row.get("matched")),
        "attendance": attendance_status,
    }
