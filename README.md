# Secure Vision Attendance

A deployable computer-vision attendance platform that combines face enrollment, image verification, video-based attendance, quality checks, embedding-based matching, and duplicate-safe attendance records behind a FastAPI API and lightweight web dashboard.

**Live demo:** https://secure-vision-attendance-1.onrender.com/

**API documentation:** https://secure-vision-attendance.onrender.com/docs

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
Face embedding extraction (OpenFace)
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
- OpenFace embeddings with a cached NumPy index
- Cosine-distance matching with a configurable threshold
- Threshold-relative match score for UI feedback
- MySQL 8 attendance persistence
- Database-level duplicate prevention using `UNIQUE(name, date)`
- Separate attendance methods: `Face Recognition` and `Video Recognition`
- Today's attendance dashboard with name, time, status, and method
- Health endpoint reporting embedding-index readiness
- Background embedding-index rebuild after enrollment
- Upload-size and video-duration limits
- Temporary-file cleanup after processing
- FastAPI Swagger/OpenAPI documentation
- Docker configuration for local/container deployment
- Automated tests for core database, quality, and liveness components

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service and embedding-index health |
| POST | `/recognition/verify` | Verify faces in an image and mark attendance |
| POST | `/recognition/video` | Process a video and mark recognized people |
| GET | `/attendance` | Retrieve attendance records |
| GET | `/attendance/today` | Retrieve today's attendance |
| POST | `/enrollment/register` | Register a person's face image |
| POST | `/enrollment/build-index` | Start embedding-index rebuild |
| GET | `/enrollment/build-index/status` | Check index-build status |
| GET | `/docs` | Interactive Swagger UI |

## Recognition logic

The application extracts an embedding for each detected face and compares it with the registered embedding index using cosine distance. A face is accepted when its distance is at or below `EMBEDDING_DISTANCE_THRESHOLD` (default `0.30`).

The displayed match score is **threshold-relative UI feedback, not a calibrated probability or accuracy percentage**. The threshold should be validated against a representative verification dataset before any high-stakes deployment.

## Video processing

Video uploads are constrained by environment-configurable limits:

- Maximum upload size: 50 MB by default
- Maximum duration: 120 seconds by default
- Sampling rate: 1 frame/second by default

Only unique recognized people are added to the video result, and the database prevents another attendance record for the same person on the same date.

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
├── docs/                    # Architecture and security documentation
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
- `EMBEDDING_DISTANCE_THRESHOLD`
- `QUALITY_BLUR_THRESHOLD`
- `MIN_BRIGHTNESS`
- `MAX_BRIGHTNESS`
- `LIVENESS_ENABLED`

The production configuration currently uses the lighter `OpenFace` embedding model to keep memory usage practical on a low-resource deployment.

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

## Limitations

- The default similarity threshold is an engineering setting, not a scientifically validated operating point.
- A match score is not a probability of identity.
- Video recognition is frame-sampling based rather than continuous tracking.
- The application currently uses MySQL 8 with connection pooling and relational constraints; production deployment should use a managed and properly secured MySQL instance.
- The current public demo should use synthetic/test enrollment data rather than sensitive real-world biometric data.

## Next production upgrades

1. Authentication and role-based access control
2. Managed MySQL deployment and database hardening
3. Encrypted biometric storage and key management
4. Calibrated FAR/FRR evaluation and threshold selection
5. Stronger presentation-attack evaluation
6. Structured audit logs and monitoring
7. Background job processing for long videos

## License

This repository is intended as a portfolio/educational project. Add an explicit open-source license before redistributing the code or allowing third-party reuse.