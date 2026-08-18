# Secure Vision Attendance

A production-oriented computer-vision attendance platform that combines face enrollment, image verification, video processing, image-quality checks, Facenet512 embedding matching, DeepFace anti-spoofing, duplicate-safe attendance, MySQL persistence, analytics, and a FastAPI API.

**Live demo:** https://secure-vision-attendance-1.onrender.com/

**API documentation:** https://secure-vision-attendance.onrender.com/docs

**Analytics API:** https://secure-vision-attendance.onrender.com/analytics/dashboard

## What problem does it solve?

Manual attendance is repetitive and difficult to audit. Basic face-recognition demos often stop at “predict a name” and do not handle image quality, presentation attacks, repeated check-ins, persistence, enrollment, or video input.

Secure Vision turns recognition into an attendance workflow:

```text
Image / Video Upload
        |
        v
Input + file validation
        |
        v
Image quality + face detection
        |
        v
DeepFace anti-spoofing / liveness gate
        |
        v
Facenet512 embedding extraction
        |
        v
Cosine-distance matching
        |
        +---- match ----> attendance business rules
        |                         |
        |                         v
        |                   MySQL record
        |
        +---- no match/spoof --> Recognition event only
```

## Key features

- Face enrollment with image-quality validation
- Face verification through a REST API
- Video attendance for MP4, MOV, AVI, MKV, and WEBM uploads
- Facenet512 embeddings with a cached NumPy index
- Cosine-distance matching with validated engineering threshold `0.375`
- DeepFace anti-spoofing with fail-closed liveness gating
- Threshold-relative match score for UI feedback
- MySQL 8 attendance persistence
- Database-level duplicate prevention using `UNIQUE(person_id, attendance_date)`
- Separate attendance methods: `Face Recognition` and `Video Recognition`
- Today's attendance dashboard
- Recognition-event logging
- Video-session tracking
- Health endpoint reporting embedding-index readiness
- Background embedding-index rebuild after enrollment
- Upload-size and video-duration limits
- Temporary-file cleanup after processing
- FastAPI Swagger/OpenAPI documentation
- Docker configuration for local/container deployment
- SQL analytics and Power BI integration through the HTTPS analytics API
- Automated tests for core database, quality, and liveness behavior

## Verified current configuration

The validated local recognition configuration is:

- **Embedding model:** `Facenet512`
- **Cosine distance threshold:** `0.375`
- **Liveness:** enabled locally and tested through the real DeepFace anti-spoofing path

The local `/recognition/verify` flow has been successfully tested with an enrolled `pappa` image. The API returned HTTP 200, correctly identified `pappa`, used Facenet512 with threshold `0.375`, reported `is_real: true`, and returned an anti-spoof score of approximately `0.99`. Duplicate attendance protection correctly returned `already_marked_today` on repeat submissions.

A FacePass benchmark was used for threshold selection. At `0.375`, the benchmark reported 79.22% genuine acceptance, 3.82% false acceptance, 96.18% unknown rejection, and 87.70% balanced accuracy. These are benchmark results, not a universal production accuracy guarantee.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service and embedding-index health |
| POST | `/recognition/verify` | Verify faces, apply liveness, and mark attendance |
| POST | `/recognition/batch-verify` | Verify multiple images |
| POST | `/recognition/video` | Process a video and mark recognized people |
| GET | `/attendance` | Retrieve attendance records |
| GET | `/attendance/today` | Retrieve today's attendance |
| POST | `/enrollment/register` | Register a person's face image |
| POST | `/enrollment/build-index` | Start embedding-index rebuild |
| GET | `/enrollment/build-index/status` | Check index-build status |
| GET | `/analytics/dashboard` | Return MySQL-backed analytics for BI/dashboard use |
| GET | `/docs` | Interactive Swagger UI |

## Recognition and liveness logic

The application detects faces, runs DeepFace anti-spoofing, and only allows an identity match when liveness succeeds. When `LIVENESS_ENABLED=true`, an unavailable or failed liveness result is fail-closed and cannot create attendance.

For live faces, the anti-spoofing result exposes `is_real=true` and the DeepFace `antispoof_score`. Spoof/unavailable results are returned as non-matches and are not allowed to create attendance.

After a live-face check succeeds, the application extracts a Facenet512 embedding and compares it with the registered embedding index using cosine distance. A face is accepted when its distance is at or below `EMBEDDING_DISTANCE_THRESHOLD`.

The displayed match score is **threshold-relative UI feedback, not a calibrated probability or accuracy percentage**. The operating threshold was selected using the project's FacePass benchmark and should be revalidated for any materially different deployment population or environment.

## Video processing

Video uploads are constrained by environment-configurable limits:

- Maximum upload size: 50 MB by default
- Maximum duration: 120 seconds by default
- Sampling rate: 1 frame/second by default

Only unique recognized people are added to the video result, and the database prevents another attendance record for the same person on the same date.

The MySQL `video_sessions` table is populated by video processing. Local verification confirmed completed sessions with sampled frames, detected faces, recognized faces, unknown faces, and processing status.

## Analytics and Power BI

The project exposes a production analytics endpoint backed by MySQL:

```text
https://secure-vision-attendance.onrender.com/analytics/dashboard
```

It provides KPI totals, daily attendance, recognition source/result breakdowns, person attendance, and video analytics.

The repository also contains:

- `docs/analytics.sql` — direct MySQL analytics queries
- `docs/POWER_BI_SETUP.md` — Power BI Web/HTTPS connector setup
- `Secure_Vision_Attendance_Analytics.pbix` — Power BI report artifact when present in the deployment workspace

The recommended BI architecture keeps MySQL credentials server-side and lets Power BI consume the HTTPS analytics API.

## Project structure

```text
secure-vision-attendance/
├── app/
│   ├── api/                 # FastAPI application and routes
│   ├── core/                # Configuration and seed-face handling
│   ├── db/                  # MySQL connection and CRUD operations
│   ├── models/              # Embedding and recognition logic
│   ├── services/            # Attendance, quality, and liveness services
│   └── utils/
├── data/
│   ├── known_faces/         # Local enrollment images
│   └── face_embeddings.npz  # Local/deployment embedding artifact
├── frontend/                # HTML/CSS/JS dashboard
├── docker/                  # Docker configuration
├── scripts/                 # Index building, migration, benchmark helpers
├── tests/                   # Automated tests
├── docs/                    # Architecture, analytics, and security documentation
├── Procfile                 # Render/Heroku-style process definition
└── requirements.txt
```

## Run locally

### 1. Create an environment

```bash
python -m venv .venv
.venv\\Scripts\\activate       # Windows PowerShell
# source .venv/bin/activate     # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

For development/testing:

```bash
pip install -r requirements-dev.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and set the MySQL credentials locally. Never commit `.env` or expose database passwords.

For the validated recognition configuration:

```env
EMBEDDING_MODEL_NAME=Facenet512
EMBEDDING_DISTANCE_THRESHOLD=0.375
LIVENESS_ENABLED=true
```

### 4. Start the API

```bash
uvicorn app.api.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 5. Start the frontend

From another terminal:

```bash
cd frontend
python -m http.server 5500
```

Open `http://localhost:5500`.

The local frontend automatically targets `http://127.0.0.1:8000`.

## Enrollment and embedding index

Registered face images are stored under `data/known_faces/` and the embedding index is generated from them.

Recommended layout:

```text
data/known_faces/
├── Uzair/
│   ├── image1.jpg
│   └── image2.jpg
└── Person2/
    └── image1.jpg
```

Build manually when needed:

```bash
python scripts/build_embeddings.py
```

The deployed application also supports rebuilding the index through the enrollment API.

## Configuration

The main runtime settings are environment variables. See `.env.example` for the supported values.

Important settings include:

- `MAX_UPLOAD_BYTES`
- `MAX_VIDEO_UPLOAD_BYTES`
- `MAX_VIDEO_SECONDS`
- `VIDEO_SAMPLE_FPS`
- `EMBEDDING_MODEL_NAME`
- `EMBEDDING_DISTANCE_THRESHOLD`
- `QUALITY_BLUR_THRESHOLD`
- `MIN_BRIGHTNESS`
- `MAX_BRIGHTNESS`
- `LIVENESS_ENABLED`

## Testing

Run:

```bash
pytest -q
```

The test suite covers core database duplicate prevention and service-level quality/liveness behavior. Recognition accuracy should be evaluated separately with a representative dataset.

The validated manual integration test is:

```text
image upload
  -> quality validation
  -> face detection
  -> DeepFace anti-spoofing
  -> Facenet512 embedding
  -> cosine matching
  -> MySQL attendance
  -> recognition-event logging
```

## Security and responsible use

Facial embeddings and face images are biometric data. Do not use this project as-is for high-stakes identity decisions.

Before real deployment, add appropriate authentication/authorization, HTTPS-only access, encrypted storage, retention/deletion controls, audit logging, consent and privacy processes, and validated FAR/FRR measurements. See `SECURITY.md`.

The liveness implementation is now technically integrated and locally verified, but presentation-attack performance must still be validated against a representative spoof dataset before making strong security claims.

## Current verification snapshot

The local MySQL-backed application has been verified with:

- 4/4 enrolled identities correctly recognized during the real enrollment self-recognition test
- Duplicate attendance protection confirmed
- Recognition events persisted to MySQL
- Video sessions persisted and completed successfully
- Facenet512 threshold `0.375` active
- DeepFace anti-spoofing active in the local API flow
- Pappa image accepted as live with an anti-spoof score of approximately `0.99`

Example local database snapshot during verification:

- 40 persons
- 43 attendance rows
- 40 people with attendance on the verification date
- 766 recognition events
- 3 completed video sessions

These figures are test-environment data and should not be treated as production capacity or accuracy claims.

## Limitations

- A match score is not a probability of identity.
- Video recognition is frame-sampling based rather than continuous tracking.
- Liveness performance needs broader presentation-attack validation before production security claims.
- The public demo should use synthetic/test enrollment data rather than sensitive real-world biometric data.
- Production use requires appropriate authentication, privacy controls, secure biometric storage, and operational monitoring.

## Production checklist

- [x] Face recognition
- [x] Facenet512 embedding index
- [x] Validated operating threshold
- [x] Image quality checks
- [x] DeepFace anti-spoofing integration
- [x] Fail-closed liveness gate
- [x] MySQL attendance persistence
- [x] Duplicate attendance protection
- [x] Recognition-event logging
- [x] Video-session tracking
- [x] Analytics SQL
- [x] HTTPS analytics API
- [x] Swagger/OpenAPI
- [x] Docker/Render configuration
- [x] Environment-based configuration
- [x] Secrets kept out of Git
- [x] Local end-to-end verification
- [ ] Production authentication/RBAC
- [ ] Managed MySQL backup/recovery validation
- [ ] Broader FAR/FRR and presentation-attack validation
- [ ] Production monitoring and alerting

## License

This repository is intended as a portfolio/educational project. Add an explicit open-source license before redistributing the code or allowing third-party reuse.
