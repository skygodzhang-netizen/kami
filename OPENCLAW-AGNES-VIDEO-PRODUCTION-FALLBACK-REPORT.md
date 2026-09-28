# OPENCLAW AGNES VIDEO PRODUCTION FALLBACK REPORT

Date: 2026-09-23

- Primary: `agnes-video-2.5-flash`
- Fallback: `agnes-video-v2.0`
- Fallback trigger: exactly HTTP 503 `video_queue_full`, three bounded attempts, and no task ID
- Primary task protection: persisted Primary task ID always wins; fallback is forbidden after acceptance
- Fallback task protection: persisted V2.0 task ID is polled and never resubmitted
- Input preservation: existing scene images used unchanged; no image-generation model invoked

## Production batch

Batch: `/home/ubuntu/.openclaw/workspace/agnes-video-pipeline/runtime/video-batches-20260923-054447`

| Scene | Primary result | Active model | Source resolution | Duration | Decode |
|---|---|---|---:|---:|---|
| 01 | QUEUE_FULL -> FALLBACK | agnes-video-v2.0 | 704x1280 | 6.041667s | PASS |
| 02 | QUEUE_FULL -> FALLBACK | agnes-video-v2.0 | 704x1280 | 6.041667s | PASS |
| 03 | PASS | agnes-video-2.5-flash | 704x1024 | 6.583333s | PASS |
| 04 | QUEUE_FULL -> FALLBACK | agnes-video-v2.0 | 704x1280 | 6.041667s | PASS |
| 05 | QUEUE_FULL -> FALLBACK | agnes-video-v2.0 | 704x1280 | 6.041667s | PASS |

Task IDs are retained in the per-scene task state and production JSON report. Credentials and signed URLs are excluded from this report.

## Final media

- Path: `/home/ubuntu/.openclaw/workspace/agnes-video-pipeline/runtime/video-batches-20260923-054447/final/black_clothing_5scene_final.mp4`
- Normalization: aspect-ratio-preserving scale + pad
- Resolution: 720x1280
- Nominal FPS: 24
- Codec: H.264 High
- Pixel format: yuv420p
- Audio: AAC stereo, 48 kHz
- Duration: 30.845333s
- ffprobe: PASS
- Full decode: PASS

## Persistence and regression

- Gateway restart: PASS
- Worker completed-state resume without network/POST: PASS
- Gateway health: PASS
- Windows Node: paired and connected, capabilities unchanged
- Telegram default/skykami: running and connected
- Agnes text provider/model regression: PASS (`agnes/agnes-3.0-flash`)
- Project A: unchanged
- Android Node: paired but currently disconnected/reapproval pending; no Android configuration was changed by this work

Backup: `/home/ubuntu/.openclaw/backups/20260923T053718Z-agnes-video-fallback`

