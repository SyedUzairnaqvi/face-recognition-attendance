"""Prepare a FacePass/LFW-derived evaluation split.

Input: an extracted dataset directory containing identity subdirectories.
Output: gallery (registered identities), known_test, unknown_test, and stress.

This script copies files; it never modifies the source dataset.
"""
from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def images(folder: Path):
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_EXTS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--identities", type=int, default=62)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    identities = [p for p in args.dataset.iterdir() if p.is_dir()]
    identities = sorted(identities)[: args.identities]
    if len(identities) < 2:
        raise SystemExit("Expected identity subdirectories in the extracted dataset.")

    for name in ("gallery", "known_test", "unknown_test", "stress"):
        (args.output / name).mkdir(parents=True, exist_ok=True)

    # One image per identity is enough to create a compact gallery.
    for identity in identities:
        files = images(identity)
        if len(files) < 2:
            continue
        rng.shuffle(files)
        gallery = files[0]
        shutil.copy2(gallery, args.output / "gallery" / f"{identity.name}__gallery{gallery.suffix.lower()}")
        for idx, path in enumerate(files[1: min(len(files), 11)], start=1):
            shutil.copy2(path, args.output / "known_test" / f"{identity.name}__{idx:03d}{path.suffix.lower()}")

    # Put identities beyond the gallery set into unknown_test when available.
    extra = identities[ max(1, len(identities) // 2) : ]
    for identity in extra:
        for idx, path in enumerate(images(identity)[:12]):
            shutil.copy2(path, args.output / "unknown_test" / f"{identity.name}__{idx:03d}{path.suffix.lower()}")

    # Duplicate a deterministic subset for duplicate-attendance testing.
    known = list((args.output / "known_test").glob("*"))
    for idx, path in enumerate(known[:100]):
        shutil.copy2(path, args.output / "stress" / f"duplicate_{idx:03d}{path.suffix.lower()}")

    print(f"Prepared evaluation at {args.output}")
    for name in ("gallery", "known_test", "unknown_test", "stress"):
        print(f"{name}: {len(images(args.output / name))}")


if __name__ == "__main__":
    main()
