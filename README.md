# 🎯 Face Recognition Attendance System

A real-time **Face Recognition-based Attendance System** built using **Computer Vision, Deep Learning, and FastAPI**.
This system detects faces, recognizes individuals, and automatically marks attendance.

---

## 🚀 Features

* 📸 Face Detection using OpenCV (Haar Cascade)
* 🧠 Face Recognition using DeepFace
* 📝 Automated Attendance Logging (CSV)
* ⚡ FastAPI Backend with REST API
* 🖼️ Image-based recognition via API
* 🔒 Duplicate attendance prevention (per day)

---

## 🛠️ Tech Stack

* Python
* FastAPI
* OpenCV
* DeepFace
* Pandas
* Uvicorn

---

## 📁 Project Structure

```
face-recognition-attendance/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── recognition.py
│   ├── models/
│   │   └── face_recognizer.py
│   ├── services/
│   │   └── attendance_service.py
│
├── data/
│   ├── known_faces/
│   └── attendance.csv
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

```bash
git clone https://github.com/YOUR_USERNAME/face-recognition-attendance.git
cd face-recognition-attendance

python -m venv .venv
.venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

---

## ▶️ Run the Application

```bash
uvicorn app.api.main:app --reload
```

Open in browser:

```
http://127.0.0.1:8000/docs
```

---

## 📸 Usage

1. Go to `/docs`
2. Use **POST /recognize**
3. Upload an image
4. System will:

   * Detect faces
   * Recognize individuals
   * Mark attendance
   * Return image with bounding boxes

---

## 🧾 Attendance Output

Stored in:

```
data/attendance.csv
```

Format:

```
Name,Date,Time
Uzair,2026-04-18,01:50:19
```

---

## 📂 Known Faces Setup

Add images of known individuals here:

```
data/known_faces/
```

Example:

```
uzair.jpg
zohair.jpg
```

---

## ⚠️ Notes

* Do not keep `attendance.csv` open while running the server
* First run may be slow due to model loading
* Accuracy depends on quality of known face images

---

## 🌐 Deployment

Deployed using **Render**

Live API:

```
https://your-app-name.onrender.com/docs
```

---

## 📌 Future Improvements

* 🎥 Real-time webcam attendance
* 📊 Dashboard (Streamlit)
* ⚡ Faster models (InsightFace)
* ☁️ Cloud storage integration

---

## 👨‍💻 Author

**Uzair**
Master’s in Data Science | Computer Vision Enthusiast

---

## ⭐ If you like this project

Give it a ⭐ on GitHub!
