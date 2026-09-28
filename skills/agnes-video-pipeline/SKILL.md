---
name: agnes-video-pipeline
description: Generate, resume, download, and verify Agnes videos through one durable production worker supporting text, keyframe, and image-reference routing.
---

# Unified Agnes Video Production Worker

Use `/home/ubuntu/.openclaw/workspace/agnes-video-pipeline/agnes_video_worker.py` for every Agnes production video. The fixed production route is `https://apihub.agnes-ai.com/v1` with `AGNES_VIDEO_KEY` from the pipeline `.env`. Never use the `.cn` endpoint or a text/image `sk-` key for this worker.

The worker chooses the mode from inputs:

- Prompt only: `text`
- `--first-frame`: `keyframe`
- `--first-frame` plus `--last-frame`: `keyframe`
- `--reference-image`: `reference`

An explicit `--mode` is allowed only when it agrees with the inputs. Audio reference, mixed image/audio reference, and arbitrary multiple keyframes are rejected until the provider schema is verified. Never provide `/dev/null`, an empty file, or a fabricated image.

Start a durable task and return after its task ID is saved:

```bash
cd /home/ubuntu/.openclaw/workspace/agnes-video-pipeline
python3 agnes_video_worker.py start --prompt "A cinematic sunrise over mountains"
python3 agnes_video_worker.py start --prompt "Animate this frame" --first-frame input.jpg
python3 agnes_video_worker.py start --prompt "Move from start to end" --first-frame start.jpg --last-frame end.jpg
python3 agnes_video_worker.py start --prompt "Use this person as identity reference, not as the first frame" --reference-image person.jpg
```

The command prints a manifest containing its state path through the selected job ID. To submit and remain attached through completion, use `run` with the same arguments. To resume without any new POST:

```bash
python3 agnes_video_worker.py resume --state runtime/unified-video-jobs/JOB/manifest.json
python3 agnes_video_worker.py resume --runtime runtime/unified-video-jobs
```

Defaults are `agnes-video-2.5-flash`, `720P`, `6` seconds, `16:9`, and one output. Supported ratios are `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, and `9:16`.

The primary request uses `POST /v1/videos`. Polling uses the production-proven `/agnesapi?video_id=...&model_name=...` route. Each task ID is atomically saved before polling. A state left in `submitting` or `submit_unknown` is never submitted again automatically because the earlier HTTP outcome could be ambiguous.

Only explicit `503 video_queue_full` or `429 rate_limit` responses are retried, with at most three attempts and 20/40 second backoff. Authentication, schema, invalid-input, and ambiguous network errors do not trigger blind resubmission. Queue-only fallback to `agnes-video-v2.0` is allowed for text mode and a single first frame. Reference mode and first-plus-last mode do not fall back because conversion would change intent.

Completion requires a nontrivial MP4, successful `ffprobe`, a valid video stream, recorded codec/dimensions/duration/pixel format/FPS, and a full `ffmpeg -xerror` decode. Keep failed state, partial diagnostics, and downloaded media for recovery.

The legacy five-scene runner remains compatible. It submits its five first-frame scenes sequentially, persists every task ID, and resumes existing tasks without duplicate POSTs. Do not delete historical batches.
