from fastapi import FastAPI
from app.db.database import init_db
from app.api.routes import recognition, attendance, health, enrollment
from app.core.config import KNOWN_FACES_DIR
from app.core.seed_faces import ensure_seed_faces

# Render Free has an ephemeral filesystem, so restore the demo enrollment image on startup.
ensure_seed_faces(KNOWN_FACES_DIR)
init_db()

app = FastAPI(
    title="Secure Vision Attendance API",
    version="2.0.0",
    description="Computer-vision identity verification and attendance API with quality checks and duplicate prevention.",
)

app.include_router(health.router)
app.include_router(recognition.router)
app.include_router(attendance.router)
app.include_router(enrollment.router)


@app.get("/")
def home():
    return {"message": "Secure Vision Attendance API is running", "docs": "/docs"}
