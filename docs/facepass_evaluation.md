# Secure Vision — FacePass/LFW Evaluation Protocol

## Purpose

Use the FacePass/LFW-derived evaluation dataset as a **benchmark only**, never as the production employee database.

Dataset: https://huggingface.co/datasets/besartshyti/facepass_eval

## Evaluation design

1. Select identities with multiple images.
2. Build a gallery/registered set from one or more images per selected identity.
3. Keep different images of those identities as the known-person test set.
4. Keep identities not present in the gallery as the unknown-person test set.
5. Run both sets through Secure Vision Batch Recognition.
6. Record TP, FP, TN, FN, precision, recall, F1, false-match rate, false-rejection rate, faces detected, processing time, and throughput.

## Important rule

Do not place the complete dataset into `data/known_faces`. Doing so would invalidate the unknown-person and generalization evaluation.

## Recommended benchmark

- 500 gallery/registered images
- 500 known-person test images
- 700 unknown-person images
- 200 mixed/quality-stress images
- 100 duplicate images
- Total target: 2,000 images

## Interpretation

The benchmark measures recognition quality and pipeline performance. It does not prove real-world employee-attendance accuracy for every camera, lighting condition, demographic, or deployment environment.
