from __future__ import annotations

from typing import Any

import numpy as np

from app.core.config import LIVENESS_ENABLED


def assess_liveness(face_obj: dict[str, Any]) -> dict[str, Any]:
    """Normalize DeepFace anti-spoofing output into the API contract."""
    if not LIVENESS_ENABLED:
        return {
            "enabled": False,
            "is_real": None,
            "score": None,
            "status": "disabled",
        }

    if not face_obj:
        return {
            "enabled": True,
            "is_real": False,
            "score": None,
            "status": "unavailable",
        }

    is_real = face_obj.get("is_real")
    score = face_obj.get("antispoof_score")

    if is_real is None:
        return {
            "enabled": True,
            "is_real": False,
            "score": None,
            "status": "unavailable",
        }

    if isinstance(score, np.generic):
        score = score.item()

    try:
        normalized_score = float(score) if score is not None else None
    except (TypeError, ValueError):
        normalized_score = None

    return {
        "enabled": True,
        "is_real": bool(is_real),
        "score": round(normalized_score, 6) if normalized_score is not None else None,
        "status": "real" if bool(is_real) else "spoof",
    }
