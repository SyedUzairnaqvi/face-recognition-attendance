# Secure Vision Attendance

A deployable computer-vision attendance platform that combines face enrollment, image verification, video-based attendance, quality checks, embedding-based matching, and duplicate-safe attendance records behind a FastAPI API and lightweight web dashboard.

**Live demo:** https://secure-vision-attendance-1.onrender.com/

**API documentation:** https://secure-vision-attendance.onrender.com/docs

**Analytics API:** https://secure-vision-attendance.onrender.com/analytics/dashboard

## What problem does it solve?

Manual attendance is repetitive and difficult to audit. Basic face-recognition demos often stop at “predict a name” and do not handle image quality, repeated check-ins, persistence, enrollment, or video input.

Secure Vision turns recognition into an attendance workflow:

```text
Image / Video Upload
        |
        v
Input + file validation
        |
        v
Image quality checks / face detection
        |
        v
Face embedding extraction (Facenet512)
        |
        v
Cosine-distance matching
        |
        +---- match ----> attendance business rules
        |                         |
        |                         v
        |                   MySQL record
        |
        +---- no match --> Unknown / not marked
```

For video attendance, the system samples frames, recognizes faces in each sampled frame, deduplicates recognized people, and records each person at most once per day.

## Key features

- Face enrollment with image-quality validation
- Face verification through a REST API
- Video attendance for MP4, MOV, AVI, MKV, and WEBM uploads
- Facenet512 embeddings with a cached NumPy index
- Cosine-distance matching with a validated engineering threshold of `0.375`
- Threshold-relative match score for UI feedback
- MySQL 8 attendance persistence
- Database-level duplicate prevention using `UNIQUE(person_id, attendance_date)`
- Separate attendance methods: `Face Recognition` and `Video Recognition`
- Today's attendance dashboard with name, time, status, and method
- Health endpoint reporting embedding-index readiness
- Background embedding-index rebuild after enrollment
- Upload-size and video-duration limits
- Temporary-file cleanup after processing
- FastAPI Swagger/OpenAPI documentation
- Docker configuration for local/container deployment
- SQL analytics and Power BI integration through the HTTPS analytics API
- Automated tests for core database, quality, and liveness components

## Verified current configuration

The current recognition configuration is:

- **Embedding model:** `Facenet512`
- **Cosine distance threshold:** `0.375`
- **Liveness:** configurable; currently disabled for the verified recognition flow

The real application flow has been tested end-to-end with four enrolled identities (`uzair`, `pappa`, `zohair`, `ammi`). All four were correctly recognized through `/recognition/verify`, and duplicate attendance protection returned `already_marked_today` on repeat submissions.

A FacePass benchmark was also used for threshold selection. At `0.375`, the benchmark reported 79.22% genuine acceptance, 3.82% false acceptance, 96.18% unknown rejection, and 87.70% balanced accuracy. These are benchmark results, not a universal production accuracy guarantee.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service and embedding-index health |
| POST | `/recognition/verify` | Verify faces in an image and mark attendance |
| POST | `/recognition/batch-verify` | Verify multiple images |
| POST | `/recognition/video` | Process a video and mark recognized people |
| GET | `/attendance` | Retrieve attendance records |
| GET | `/attendance/today` | Retrieve today's attendance |
| POST | `/enrollment/register` | Register a person's face image |
| POST | `/enrollment/build-index` | Start embedding-index rebuild |
| GET | `/enrollment/build-index/status` | Check index-build status |
| GET | `/analytics/dashboard` | Return MySQL-backed analytics for BI/dashboard use |
| GET | `/docs` | Interactive Swagger UI |

## Recognition logic

The application extracts an embedding for each detected face and compares it with the registered embedding index using cosine distance. A face is accepted when its distance is at or below `EMBEDDING_DISTANCE_THRESHOLD`.

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
- `Secure_Vision_Attendance_Analytics.pbix` — Power BI report artifact

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

### 3. Start the API

```bash
uvicorn app.api.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 4. Start the frontend

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

## Security and responsible use

Facial embeddings and face images are biometric data. Do not use this demo as-is for high-stakes identity decisions.

Before a real deployment, add appropriate authentication/authorization, HTTPS-only access, encrypted storage, retention/deletion controls, audit logging, consent and privacy processes, and a validated recognition threshold. See [`SECURITY.md`](SECURITY.md).

The liveness service is present as a configurable component; `LIVENESS_ENABLED` should only be enabled after validating its behavior and resource requirements for the target deployment.

## Current verification snapshot

The local MySQL-backed application has been verified with:

- 4/4 real enrolled identities correctly recognized through `/recognition/verify`
- Duplicate attendance protection confirmed
- Recognition events persisted to MySQL
- Video sessions persisted and completed successfully
- Facenet512 threshold `0.375` active in the current configuration

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
- Liveness is currently disabled in the verified flow and must be validated before claiming presentation-attack resistance.
- The public demo should use synthetic/test enrollment data rather than sensitive real-world biometric data.
- Production use requires appropriate authentication, privacy controls, secure biometric storage, and operational monitoring.

## Next production upgrades

1. Validate and enable an appropriate liveness/presentation-attack control
2. Add authentication and role-based access control
3. Harden managed MySQL deployment and backups
4. Add encrypted biometric storage and key management
5. Expand FAR/FRR and demographic/environment validation
6. Add structured audit logs and monitoring
7. Add background job processing for long videos

## License

This repository is intended as a portfolio/educational project. Add an explicit open-source license before redistributing the code or allowing third-party reuse.
