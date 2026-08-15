from unittest.mock import patch

from deepface.modules.exceptions import FaceNotDetected

from app.models.embedding_engine import _extract_live_faces
from app.services.liveness_service import assess_liveness


def test_liveness_live_face():
    result = assess_liveness({"is_real": True, "antispoof_score": 0.91})
    assert result["enabled"] is True
    assert result["is_real"] is True
    assert result["status"] == "live"


def test_liveness_spoof_face():
    result = assess_liveness({"is_real": False, "antispoof_score": 0.08})
    assert result["enabled"] is True
    assert result["is_real"] is False
    assert result["status"] == "spoof"


def test_no_face_is_handled_as_empty_result():
    with patch("app.models.embedding_engine.DeepFace.extract_faces", side_effect=FaceNotDetected("no face")):
        assert _extract_live_faces("missing-face.jpg") == []
