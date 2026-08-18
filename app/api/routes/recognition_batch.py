from __future__ import annotations

from time import perf_counter

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import EMBEDDING_INDEX_PATH
from app.services.batch_recognition_service import (
    bulk_store_results,
    recognize_image_bytes,
)
from app.services.quality_service import assess_image


router = APIRouter(prefix="/recognition", tags=["Recognition"])

MAX_BATCH_FILES = 50
MAX_BATCH_BYTES = 50 * 1024 * 1024


@router.post("/batch-verify")
async def batch_verify(files: list[UploadFile] = File(...)):
    """Process up to 50 images in one request with cached recognition and bulk MySQL writes."""
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one image")

    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=413,
            detail=f"Maximum {MAX_BATCH_FILES} images per batch. The web app automatically chunks larger folders.",
        )

    if not EMBEDDING_INDEX_PATH.exists():
        raise HTTPException(status_code=503, detail="Embedding index is not ready")

    started = perf_counter()
    total_bytes = 0
    all_results: list[dict] = []
    file_results: list[dict] = []

    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            file_results.append({"file": file.filename or "unknown", "status": "rejected", "reason": "not_an_image"})
            continue

        data = await file.read()
        total_bytes += len(data)
        if total_bytes > MAX_BATCH_BYTES:
            raise HTTPException(status_code=413, detail="Batch exceeds 50 MB")
        if not data:
            file_results.append({"file": file.filename or "unknown", "status": "rejected", "reason": "empty_image"})
            continue

        image_array = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            file_results.append({"file": file.filename or "unknown", "status": "rejected", "reason": "invalid_image"})
            continue

        quality = assess_image(image)
        if not quality.get("accepted", False):
            file_results.append({
                "file": file.filename or "unknown",
                "status": "rejected",
                "reason": "image_quality",
                "quality": quality,
            })
            continue

        try:
            recognitions = recognize_image_bytes(data)
        except Exception as exc:
            print(f"Batch recognition failure for {file.filename}: {type(exc).__name__}: {exc}")
            file_results.append({
                "file": file.filename or "unknown",
                "status": "error",
                "reason": "recognition_failed",
            })
            continue

        for recognition in recognitions:
            recognition["source_file"] = file.filename or "unknown"
            all_results.append(recognition)

        file_results.append({
            "file": file.filename or "unknown",
            "status": "processed" if recognitions else "no_face_detected",
            "faces": len(recognitions),
            "matched": sum(1 for item in recognitions if item.get("matched")),
            "recognitions": recognitions,
            "quality": quality,
        })

    storage = bulk_store_results(all_results)
    elapsed = max(perf_counter() - started, 0.001)

    return {
        "status": "completed",
        "files_received": len(files),
        "files_processed": sum(1 for item in file_results if item["status"] == "processed"),
        "faces_detected": len(all_results),
        "matched_faces": storage["matched_faces"],
        "unknown_faces": storage["unknown_faces"],
        "events_saved": storage["saved_events"],
        "attendance": storage["attendance"],
        "elapsed_seconds": round(elapsed, 2),
        "throughput_files_per_second": round(len(files) / elapsed, 2),
        "throughput_faces_per_second": round(len(all_results) / elapsed, 2),
        "results": file_results,
    }
