import os, json, glob

WS = os.path.expanduser("~/.openclaw/workspace")
SKILL = os.path.join(WS, "skills", "agnes-video-pipeline")
PIPE = os.path.join(WS, "agnes-video-pipeline")

os.makedirs(os.path.join(SKILL, "docs"), exist_ok=True)
os.makedirs(os.path.join(SKILL, "examples"), exist_ok=True)
os.makedirs(os.path.join(SKILL, "scripts"), exist_ok=True)

# 1) Copy the proven pipeline scripts into the skill (so the skill is self-contained)
import shutil
for f in ["pipeline.py", "pipeline_concat.py", "run_pipeline.py", "scenes.json"]:
    src = os.path.join(PIPE, f)
    if os.path.exists(src):
        shutil.copyfile(src, os.path.join(SKILL, "scripts", f))

skill_md = """# Agnes 5-Scene Video Pipeline

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
"""

workflow_md = """# Production Workflow — Agnes 5-Scene Video

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
"""

failure_md = """# Failure Handling Rules

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
"""

example = json.load(open(os.path.join(PIPE, "scenes.json")))
with open(os.path.join(SKILL, "examples", "five_scene_example.json"), "w") as f:
    json.dump(example, f, indent=2, ensure_ascii=False)

with open(os.path.join(SKILL, "SKILL.md"), "w") as f:
    f.write(skill_md)
with open(os.path.join(SKILL, "README.md"), "w") as f:
    f.write("# Agnes Video Pipeline Skill\n\nSee SKILL.md, docs/production-workflow.md, docs/failure-handling.md, examples/five_scene_example.json, scripts/*.\n")
with open(os.path.join(SKILL, "docs", "production-workflow.md"), "w") as f:
    f.write(workflow_md)
with open(os.path.join(SKILL, "docs", "failure-handling.md"), "w") as f:
    f.write(failure_md)

# 2) Memory persistence (additive) — memory-core indexes workspace memory.
mem_dir = os.path.join(WS, "memory")
os.makedirs(mem_dir, exist_ok=True)
mem_file = os.path.join(mem_dir, "agnes-video-pipeline-workflow.md")
if not os.path.exists(mem_file):
    mem_content = """# Memory: Agnes 五场景视频生产标准流程

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
"""
    with open(mem_file, "w") as f:
        f.write(mem_content)
    print("memory file created:", mem_file)
else:
    print("memory file already exists (skipped)")

print("SKILL created at", SKILL)
print("files:", sorted(os.path.relpath(os.path.join(r, x), SKILL) for r, _, fs in os.walk(SKILL) for x in fs))
