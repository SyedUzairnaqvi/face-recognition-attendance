from __future__ import annotations

from typing import Any

import numpy as np

from app.core.config import LIVENESS_ENABLED


def assess_liveness(face_obj: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized liveness decision from DeepFace face extraction output.

    DeepFace performs the anti-spoofing inference when ``anti_spoofing=True``.
    This service only turns its result into a stable API shape.
    """
    if not LIVENESS_ENABLED:
        return {"enabled": False, "is_real": None, "score": None, "status": "disabled"}

    is_real = face_obj.get("is_real")
    score = face_obj.get("antispoof_score")

    if is_real is None:
        return {"enabled": True, "is_real": False, "score": None, "status": "unavailable"}

    if isinstance(score, np.generic):
        score = score.item()

    return {
        "enabled": True,
        "is_real": bool(is_real),
        "score": round(float(score), 4) if score is not None else None,
        "status": "live" if bool(is_real) else "spoof",
    }
