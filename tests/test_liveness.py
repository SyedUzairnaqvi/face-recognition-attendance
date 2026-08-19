import app.services.liveness_service as liveness_service
from unittest.mock import patch

from app.models.embedding_engine import _extract_live_faces


def test_liveness_live_face(monkeypatch):
    monkeypatch.setattr(liveness_service, "LIVENESS_ENABLED", True)
    result = liveness_service.assess_liveness({"is_real": True, "antispoof_score": 0.91})
    assert result["enabled"] is True
    assert result["is_real"] is True
    assert result["status"] == "real"


def test_liveness_spoof_face(monkeypatch):
    monkeypatch.setattr(liveness_service, "LIVENESS_ENABLED", True)
    result = liveness_service.assess_liveness({"is_real": False, "antispoof_score": 0.08})
    assert result["enabled"] is True
    assert result["is_real"] is False
    assert result["status"] == "spoof"


def test_no_face_is_handled_as_empty_result():
    with patch(
        "app.models.embedding_engine.DeepFace.extract_faces",
        side_effect=RuntimeError("no face"),
    ):
        assert _extract_live_faces("missing-face.jpg") == []
