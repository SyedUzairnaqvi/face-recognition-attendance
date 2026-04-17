from app.services.attendance_service import mark_attendance
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

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image = cv2.imread(temp_path)

    people = recognize_faces(temp_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    faces = face_cascade.detectMultiScale(gray, 1.1, 5)

    for (x, y, w, h), name in zip(faces, people or ["Unknown"] * len(faces)):
        cv2.rectangle(image, (x,y), (x+w,y+h), (0,255,0), 2)

        cv2.putText(
            image,
            name,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0,255,0),
            2
        )

    _, buffer = cv2.imencode(".jpg", image)

    return StreamingResponse(io.BytesIO(buffer), media_type="image/jpeg")