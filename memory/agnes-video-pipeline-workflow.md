# Memory: Agnes 五场景视频生产标准流程

## Canonical workflow (repeatable)
- 5 reference images + 5 prompts -> 5 independent Agnes video tasks.
- Mapping: Scene N = Image N + Prompt N. One reference image = one scene
  (single-reference image-to-video). Do NOT require first+last frames;
  do NOT fabricate tail frames.
- Agnes provider: `https://apihub.agnes-ai.cn/v1`; video models
  `agnes-video-2.5-flash` (primary) and `agnes-video-v2.0` (fallback).
  API key read at runtime from `~/.openclaw/openclaw.json`
  (`models.providers.agnes.apiKey`) or `AGNES_API_KEY`; NEVER written to
  logs/manifests/reports/memory/skill.

## Submission + monitoring
- Submit all 5 in parallel (independent tasks).
- Poll each independently. A single scene failure MUST NOT abort the batch;
  keep collecting all task states.
- Persist per batch under `runtime/video-batches-<ts>/` with
  input/ requests/ tasks/ videos/ logs/ reports/ final/ + manifest.json.

## Per task record
scene_id, prompt, source_image, model, request payload, task_id, submit_time,
poll_time, status, video_url, local_file, error, duration, resolution, codec,
fps, audio, file_size.

## Downstream (all proven on Ubuntu)
- download -> ffprobe (duration/width/height/codec/profile/pix_fmt/fps/SAR/DAR/audio/size).
- concat Scene 01->05 in EXACT order. stream-copy if clips compatible;
  else filter re-encode. 704x1280 -> 720x1280 is SCALE normalization (no crop).
- final: 720x1280, 9:16, H.264, yuv420p, 24fps, ~30s.
- full decode verification (ffmpeg -f null) required before claiming success.

## Retention
- Never delete the 5 source clips, the final MP4, logs, or evidence.
- No auto-cleanup on failure.

## Verified real results (2026-09-18)
- Agnes v2.0 text-to-video on Ubuntu -> HTTP 200 -> completed -> downloaded
  -> ffprobe 704x1280/h264/yuv420p/24fps.
- 704->720 normalize + concat -> 720x1280/9:16/h264/yuv420p/24fps final,
  full decode check RC 0.
- BLOCKED: 5-scene image-to-video returns HTTP 429 (free-tier video quota)
  and gateway 400 on oversized data-uri bodies. Clearing these needs a
  Token Plan / key / gateway / timeout change (out of scope).
