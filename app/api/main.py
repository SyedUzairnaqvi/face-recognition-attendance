from fastapi import FastAPI
from app.api.routes import recognition

app = FastAPI()

app.include_router(recognition.router)

@app.get("/")
def home():
    return {"message": "Face Recognition API is running"}