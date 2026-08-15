import numpy as np
from app.services.quality_service import assess_image


def test_quality_returns_expected_fields():
    image = np.full((100, 100, 3), 128, dtype=np.uint8)
    result = assess_image(image)
    assert "accepted" in result
    assert "blur_score" in result
    assert "brightness" in result
