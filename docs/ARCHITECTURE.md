# Architecture

```text
                         +----------------------+
                         |   Web Dashboard      |
                         | HTML / CSS / JS      |
                         +----------+-----------+
                                    |
                              REST / multipart
                                    |
                                    v
                         +----------------------+
                         |      FastAPI API      |
                         +----------+-----------+
                                    |
              +---------------------+---------------------+
              |                     |                     |
              v                     v                     v
       Recognition            Video Recognition      Enrollment
       image verify           frame sampling         register/rebuild
              |                     |                     |
              +---------------------+---------------------+
                                    |
                                    v
                         +----------------------+
                         | Face detection       |
                         | Quality checks       |
                         | OpenFace embeddings  |
                         | Cosine matching      |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Attendance service   |
                         | duplicate-safe rules |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | SQLite attendance DB |
                         +----------------------+

Registered face images ---> embedding index (.npz)
```

## Main request flows

### Image verification

1. Validate uploaded image and size.
2. Run image-quality checks.
3. Detect faces.
4. Generate OpenFace embedding for each face.
5. Compare against the cached embedding index with cosine distance.
6. Apply the configured threshold.
7. Mark matched identities through the attendance service.
8. SQLite prevents a second record for the same person/date.

### Video attendance

1. Validate video type, size, and duration.
2. Decode the video with OpenCV.
3. Sample frames at the configured rate.
4. Detect and recognize faces in sampled frames.
5. Count unmatched detections separately.
6. Deduplicate recognized identities within the video request.
7. Record attendance once per recognized person.
8. Return recognition and video-processing metadata.

## Deployment

The backend is served by Uvicorn using the repository `Procfile`. The frontend is a static HTML/CSS/JS application and can be served independently. The production configuration favors OpenFace to reduce memory pressure on a low-resource Render instance.