import cv2
from app.core.config import QUALITY_BLUR_THRESHOLD, MIN_BRIGHTNESS, MAX_BRIGHTNESS


def assess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())

    issues = []
    if blur_score < QUALITY_BLUR_THRESHOLD:
        issues.append("image_too_blurry")
    if brightness < MIN_BRIGHTNESS:
        issues.append("image_too_dark")
    if brightness > MAX_BRIGHTNESS:
        issues.append("image_too_bright")

    return {
        "accepted": not issues,
        "blur_score": round(blur_score, 2),
        "brightness": round(brightness, 2),
        "issues": issues,
    }
