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
                         |      MySQL 8          |
                         | persons               |
                         | attendance            |
                         | recognition_events    |
                         | video_sessions        |
                         +----------------------+

Registered face images ---> embedding index (.npz)
