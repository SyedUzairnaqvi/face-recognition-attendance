# Secure Vision-Based Attendance & Identity Verification Platform

An image-based attendance platform using computer vision and deep face recognition, exposed through a FastAPI REST API. The system adds image-quality gating, DeepFace anti-spoofing/liveness checks, cached face embeddings, explicit similarity-threshold decisions, SQLite-backed attendance records, and database-level duplicate prevention.

## Problem

Manual attendance and basic image-based recognition systems can be slow, difficult to audit, and vulnerable to duplicate check-ins or unreliable recognition under poor image conditions. This project focuses on building a practical verification workflow rather than treating face recognition as a single prediction step.

## Current pipeline

```text
Uploaded image
  -> Image validation
  -> Blur/brightness quality check
  -> Face detection + liveness / anti-spoofing
  -> Face embedding extraction
  -> Cosine similarity against registered embeddings
  -> Similarity-threshold decision
  -> Attendance business rule
  -> SQLite persistence
  -> REST API response
```

## Features implemented

- OpenCV-based image validation and quality scoring
- DeepFace `Facenet512` face embeddings
- Cached embedding index stored as compressed NumPy data
- Cosine-distance identity matching
- Explicit threshold-based match decisions
- Threshold-relative match score (not a calibrated probability)
- Duplicate attendance prevention using a database UNIQUE constraint on `(name, date)`
- SQLite persistence instead of a mutable CSV file
- REST endpoints for recognition and attendance history
- FastAPI Swagger documentation
- Health endpoint reporting embedding-index readiness
- Upload-size and content-type validation
- Temporary-file cleanup
- DeepFace anti-spoofing gate before identity matching
- Multi-face processing in a single image
- Per-face liveness result and spoof rejection reason

## Build the embedding index

Place registered images under `data/known_faces/`.

For multiple images per person, the recommended layout is:

```text
data/known_faces/
  Uzair/
    image1.jpg
    image2.jpg
  Alice/
    image1.jpg
    image2.jpg
```

Then run:

```bash
python scripts/build_embeddings.py
```

The generated `data/face_embeddings.npz` is a local artifact and should not be committed if it contains real biometric data.

## Run locally

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python scripts/build_embeddings.py
uvicorn app.api.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## API

- `GET /health`
- `POST /recognition/verify`
- `GET /attendance`
- `GET /attendance/today`
- `GET /docs`

## Recognition decision

The system uses cosine distance between the query embedding and registered embeddings. A match is accepted when the distance is below the configured threshold.

The current default threshold is an **engineering starting point**, not a validated production threshold. It must be calibrated using a held-out verification dataset before deployment.

## Evaluation plan

Before making performance claims, benchmark:

- identification/verification precision, recall and F1
- false acceptance rate (FAR)
- false rejection rate (FRR)
- recognition latency
- quality rejection rate under blur/lighting changes
- duplicate-prevention correctness
- threshold sensitivity

## Security notes and limitations

This version now includes a DeepFace anti-spoofing/liveness gate before identity matching. DeepFace exposes an `anti_spoofing=True` mode that returns an `is_real` result and an anti-spoofing score; this project rejects a face before identity matching when the liveness gate reports a spoof.

The liveness gate improves protection against simple photo/screen presentation attacks, but it is **not a guarantee against every presentation attack** and must be evaluated on representative spoof data before production deployment.

The application is still image-based rather than a dedicated webcam product. It also does not claim PostgreSQL, JWT authentication, FAISS, or calibrated recognition probabilities. The recognition threshold remains an engineering starting point and should be calibrated using a held-out verification dataset.

## Responsible use

Facial data is biometric information. A production deployment should use explicit consent, access control, encryption, retention/deletion policies, audit logs, and appropriate organizational/legal review.
