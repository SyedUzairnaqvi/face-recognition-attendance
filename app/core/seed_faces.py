from __future__ import annotations

import base64
from pathlib import Path

# Demo enrollment faces embedded in the source so Render Free can recreate
# the registered face files after a restart (its local filesystem is ephemeral).
_SEED_FACES = {
    "uzair/uzair_1.jpg": 'REPLACE_ME_1',
    "uzair/uzair_2.jpg": 'REPLACE_ME_2',
}


def ensure_seed_faces(known_faces_dir: Path) -> None:
    """Restore demo face images if they are missing."""
    for relative_path, encoded in _SEED_FACES.items():
        target = known_faces_dir / relative_path
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(base64.b64decode(encoded))
