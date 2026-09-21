# Agnes 5-Scene Video Pipeline

Turn 5 reference images + 5 scene prompts into 5 independent Agnes video
generations (single-reference image-to-video, ~6s each), with parallel
submit, independent polling, failure isolation, download, ffprobe,
Scene 01->05 concat, 720x1280 / 9:16 / H.264 / yuv420p / 24fps
normalization, full decode verification, and a production report.

## When to use
- User provides 5 scene reference images + 5 scene prompts.
- Goal: one ~30s 9:16 vertical MP4 built from 5 independent scene clips.

## Inputs
- 5 images: `input/scene01.jpg` .. `input/scene05.jpg`
- 5 prompts: `scenes.json` (see examples/five_scene_example.json)
- Mapping: Scene N -> Image N + Prompt N. One reference image = one scene.
  Do NOT require first+last frames; do NOT fabricate tail frames.

## Agnes capability (audited on Ubuntu)
- Provider `agnes` is registered: baseUrl `https://apihub.agnes-ai.cn/v1`.
- API key is read at runtime from `~/.openclaw/openclaw.json`
  (`models.providers.agnes.apiKey`) or `AGNES_API_KEY`. NEVER printed.
- Video models: `agnes/agnes-video-2.5-flash` (primary) and
  `agnes/agnes-video-v2.0` (fallback). Both in the allowlist.
- API contract (from the agnes-video plugin + skill):
  - `POST /v1/videos` body `{model, prompt, seconds, size, aspect_ratio,
    resolution, images:[{url}]}`
  - `videoId = id|task_id|data.id|data.task_id`
  - poll `GET /v1/videos/{videoId}`; success on status in
    completed/success OR video_url present; fail on failed/error/cancelled.
  - image-to-video uses a remote/available image URL.

## Pipeline (separated stages, all retained on failure)
1. **submit** 5 independent tasks (parallel, single-worker-per-scene).
2. **poll** independently; a single scene failure NEVER aborts the batch.
3. **download** each completed clip.
4. **inspect** each with ffprobe -> manifest.
5. **concat** Scene 01->05 (stream-copy if all clips share codec/res/fps;
   else filter re-encode; 704->720 scale normalization).
6. **verify** final MP4: decode check + 5 scene keyframe boundaries.
7. **report** production-report.json + .md.

Every batch writes to `runtime/video-batches-YYYYMMDD-HHMMSS/` with
input/ requests/ tasks/ videos/ logs/ reports/ final/ + manifest.json.
Nothing is deleted on failure.

## How to run
```
cd ~/.openclaw/workspace/agnes-video-pipeline
python3 run_pipeline.py
```

## Known blockers (real, observed 2026-09-18)
- Agnes free-tier video-generation quota returns **HTTP 429**
  `rate_limit_exceeded` ("free users ... Upgrade to a Token Plan") for
  image-to-video and for `agnes-video-2.5-flash`.
- The gateway rejects oversized in-body data-URIs -> **HTTP 400
  `invalid_json`**. Use a remote/available image URL, not a giant base64.
- `agnes-video-v2.0` text-to-video IS available (HTTP 200 -> completed).
- Downstream chain (download -> ffprobe -> 704->720 -> concat -> verify)
  is proven working on Ubuntu with real salvaged Agnes clips.
- These blockers require a Token Plan upgrade / key change / gateway or
  timeout change to clear, which are OUT OF SCOPE for this task.

## Failure handling
See docs/failure-handling.md (cases A-J).
