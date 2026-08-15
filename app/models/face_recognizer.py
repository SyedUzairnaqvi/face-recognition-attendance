from app.models.embedding_engine import recognize_with_embeddings


def recognize_faces(img_path, db_path=None):
    """Backward-compatible wrapper around the cached embedding recognizer."""
    return recognize_with_embeddings(str(img_path))
