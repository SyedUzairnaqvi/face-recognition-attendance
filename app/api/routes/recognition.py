from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import shutil
import cv2
import io

from app.models.face_recognizer import recognize_faces
from app.services.attendance_service import mark_attendance

router = APIRouter()

@router.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    temp_path = "temp.jpg"

    # Save uploaded image
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Read image
    image = cv2.imread(temp_path)

    if image is None:
        return {"error": "Invalid image"}

    # 🔥 Face recognition
    result = recognize_faces(temp_path)

    print("RAW RESULT:", result)

    # Handle both dict and list outputs
    if isinstance(result, dict):
        people = result.get("result", [])
    else:
        people = result

    print("PEOPLE:", people)

    # 🔥 Mark attendance
    for name in people:
        print("CHECKING:", name)
        if name != "Unknown":
            mark_attendance(name)

    # Convert to grayscale for detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    faces = face_cascade.detectMultiScale(gray, 1.1, 5)

    # Draw bounding boxes + names safely
    for i, (x, y, w, h) in enumerate(faces):
        name = people[i] if i < len(people) else "Unknown"

        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.putText(
            image,
            name,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    # Encode image
    _, buffer = cv2.imencode(".jpg", image)

    return StreamingResponse(io.BytesIO(buffer), media_type="image/jpeg")