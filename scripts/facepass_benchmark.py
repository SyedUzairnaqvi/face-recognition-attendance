"""Run a full FacePass benchmark against the local Secure Vision API.

Usage:
    python scripts/facepass_benchmark.py --base-url http://127.0.0.1:8000 --benchmark-dir path\to\benchmark

The script sends known and unknown images to /recognition/verify and reports
recognition accuracy and throughput. It does not modify the GitHub repository
or upload the benchmark dataset.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import requests

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def files(folder: Path):
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_EXTS)


def run_group(base_url: str, folder: Path, expected: str, timeout: int):
    rows = []
    for i, path in enumerate(files(folder), 1):
        start = time.perf_counter()
        try:
            with path.open("rb") as fh:
                response = requests.post(
                    f"{base_url.rstrip('/')}/recognition/verify",
                    files={"file": (path.name, fh, "image/png")},
                    timeout=timeout,
                )
            elapsed = time.perf_counter() - start
            data = response.json()
            recognitions = data.get("recognitions", [])
            matched = [r for r in recognitions if r.get("matched")]
            is_known = bool(matched)
            correct = is_known if expected == "known" else not is_known
            rows.append({
                "file": path.name,
                "expected": expected,
                "http": response.status_code,
                "known": is_known,
                "correct": correct,
                "elapsed": elapsed,
                "error": None,
            })
        except Exception as exc:
            rows.append({
                "file": path.name,
                "expected": expected,
                "http": None,
                "known": False,
                "correct": False,
                "elapsed": time.perf_counter() - start,
                "error": f"{type(exc).__name__}: {exc}",
            })
        if i % 25 == 0 or i == len(files(folder)):
            print(f"{expected}: {i}/{len(files(folder))}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--benchmark-dir", type=Path, required=True)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--output", type=Path, default=Path("facepass_benchmark_results.json"))
    args = ap.parse_args()

    known_dir = args.benchmark_dir / "known_test"
    unknown_dir = args.benchmark_dir / "unknown_test"
    if not known_dir.exists() or not unknown_dir.exists():
        raise SystemExit("benchmark/known_test and benchmark/unknown_test are required")

    start = time.perf_counter()
    known = run_group(args.base_url, known_dir, "known", args.timeout)
    unknown = run_group(args.base_url, unknown_dir, "unknown", args.timeout)
    total_elapsed = time.perf_counter() - start
    rows = known + unknown

    tp = sum(r["expected"] == "known" and r["known"] for r in rows)
    fn = sum(r["expected"] == "known" and not r["known"] for r in rows)
    tn = sum(r["expected"] == "unknown" and not r["known"] for r in rows)
    fp = sum(r["expected"] == "unknown" and r["known"] for r in rows)
    errors = sum(r["error"] is not None for r in rows)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fmr = fp / (fp + tn) if fp + tn else 0.0
    fnr = fn / (fn + tp) if fn + tp else 0.0

    result = {
        "dataset": "FacePass/LFW-derived benchmark",
        "known_test_images": len(known),
        "unknown_test_images": len(unknown),
        "tp": tp, "fn": fn, "tn": tn, "fp": fp,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_match_rate": fmr,
        "false_rejection_rate": fnr,
        "errors": errors,
        "total_elapsed_seconds": total_elapsed,
        "images_per_second": len(rows) / total_elapsed if total_elapsed else 0,
        "mean_request_seconds": statistics.mean([r["elapsed"] for r in rows]) if rows else 0,
        "rows": rows,
    }
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
    print(f"Saved detailed results to {args.output}")


if __name__ == "__main__":
    main()
