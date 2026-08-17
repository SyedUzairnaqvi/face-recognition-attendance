# Security and privacy notes

## Biometric data

Face images and derived embeddings are biometric information. Treat both as sensitive data.

## Database

The application uses MySQL 8 for attendance, person, recognition-event, and video-session persistence.

The application connects through a MySQL connection pool and reads database credentials from environment variables.

Database credentials must never be committed to Git.

## Before production use

- Obtain appropriate consent and define a lawful purpose.
- Restrict enrollment, recognition, and attendance administration to authorized users.
- Use HTTPS and authenticated API access.
- Encrypt biometric data at rest and in backups.
- Define retention and deletion rules for face images, embeddings, and attendance records.
- Keep audit logs for enrollment, recognition, administrative changes, and deletions.
- Do not expose raw biometric files through a public static directory.
- Validate recognition thresholds on representative genuine/impostor data.
- Measure false acceptance and false rejection rates before relying on the system for consequential decisions.
- Evaluate presentation attacks and liveness behavior with representative spoof data.
- Provide a manual correction/appeal process for attendance errors.
- Use a managed and properly secured MySQL deployment for production.
- Restrict the application database account to only the permissions required by the application.

## Current portfolio-demo scope

The current application is designed as a portfolio/development system.

It uses MySQL 8 for relational application data, a configurable cosine-distance threshold, and a lightweight OpenFace embedding model for a resource-constrained deployment.

These choices are practical for the current demonstration environment but should not be interpreted as production security guarantees.

The public demo should avoid storing sensitive real-world biometric data. Use test identities when demonstrating the application publicly.

## Configuration caution

Keep secrets and deployment credentials in the hosting provider's environment-variable settings.

Never commit `.env`, API keys, database credentials, or private certificates.

The local `.env` file is intentionally excluded from Git.