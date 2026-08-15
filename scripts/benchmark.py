"""Simple latency benchmark for a local recognition test image."""
import statistics
import sys
import time
from app.core.config import KNOWN_FACES_DIR
from app.models.face_recognizer import recognize_faces

if len(sys.argv) != 2:
    raise SystemExit("Usage: python scripts/benchmark.py path/to/test.jpg")

path = sys.argv[1]
times = []
for _ in range(3):
    start = time.perf_counter()
    recognize_faces(path, KNOWN_FACES_DIR)
    times.append(time.perf_counter() - start)

print(f"Runs: {len(times)}")
print(f"Mean latency: {statistics.mean(times):.3f}s")
print(f"Min latency: {min(times):.3f}s")
print(f"Max latency: {max(times):.3f}s")
