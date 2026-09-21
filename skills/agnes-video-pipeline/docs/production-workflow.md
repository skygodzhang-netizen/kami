# Production Workflow — Agnes 5-Scene Video

## Standard flow (repeatable)
1. Place 5 images at `input/scene01..05.jpg`.
2. Fill `scenes.json` (5 prompts, model=agnes-video-2.5-flash primary,
   fallback agnes-video-v2.0, size=720x1280, aspect_ratio=9:16, seconds=6).
3. `python3 run_pipeline.py`.
4. Inspect `runtime/<batch>/manifest.json` (per-scene task_id/status/error).
5. On all-5-completed: `runtime/<batch>/final/black_clothing_5scene_final.mp4`
   is the ~30s 9:16 H.264 yuv420p 24fps output.
6. Read `runtime/<batch>/reports/production-report.md`.

## Non-negotiables
- 5 independent tasks; parallel submit; independent poll.
- Single-scene failure MUST NOT abort the batch (error isolation).
- 704x1280 -> 720x1280 is SCALE normalization (no crop), recorded, not silent.
- Stream-copy when clips are compatible; re-encode when not. Never fail on mismatch.
- Retain all 5 source clips + final + logs + evidence. No auto-cleanup.
- Full decode verification required before any "VERIFIED" claim.
- API key never written to logs / manifests / reports / memory / skill.
