# Failure Handling Rules

| Case | Meaning | Handling |
|------|---------|----------|
| A | all 5 succeed | concat all 5 in Scene 01->05 order; verify; PRODUCTION VERIFIED |
| B | one task fails | keep polling the others; report that scene as failed; batch continues |
| C | one task timeout | mark timeout after poll budget; others continue; re-run just that scene |
| D | download failed | re-try download; keep video_url; mark scene download_failed |
| E | corrupt clip | ffprobe fails -> mark inspect_failed; exclude from concat |
| F | codec mismatch across clips | automatic switch to filter re-encode (never fail on mismatch) |
| G | 704x1280 input | normalize via scale to 720x1280 (recorded), not crop |
| H | a clip has no audio | concat video-only (a=0); do NOT add BGM/voice/music |
| I | ffmpeg concat fails | keep ffmpeg_last.log + inputs; do not delete; report |
| J | final decode verification fails | keep all evidence; report NOT VERIFIED + reason |

## Hard rule
No single-scene failure may cause the batch to exit early or lose the state
of the other scenes. All task_ids, statuses, requests, responses, errors,
timestamps and logs are persisted per batch.
