from app.core.config import KNOWN_FACES_DIR
from app.models.embedding_engine import build_embedding_index


if __name__ == "__main__":
    result = build_embedding_index(KNOWN_FACES_DIR)
    print("Embedding index built successfully")
    for key, value in result.items():
        print(f"{key}: {value}")
