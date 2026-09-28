# OPENCLAW VIDEO PIPELINE ALIGNMENT REPORT

Date: 2026-09-23

## Agnes Code Video Path

- Installed client: `D:\Users\11561\AppData\Local\Programs\AgnesCode\AgnesCode.exe`; runtime `resources\bin\agnesd.exe`.
- AgnesCode exposes `agnes_aigc__image_to_video`; it accepts a local path, HTTPS URL, or prior-generation metadata and owns create, poll, and download outside the text-model request.
- The September 18 five-scene AgnesCode session used its shell/developer execution path to operate the Ubuntu production pipeline. Logs show `.com` `/agnesapi?video_id=...` polling. No evidence showed a conflicting wire schema.

## OpenClaw Old Video Path

- Provider: `/home/ubuntu/.openclaw/plugins/agnes-video/index.js`.
- It always built `mode: "text"`, then added `images: [{url: ...}]` when input images existed.
- It returned a video item without the required `mimeType`, consistent with the historical `Cannot read properties of undefined (reading 'type')` result-processing failure.
- Its provider call performed submit and the whole poll loop in one invocation; task state was not durable enough to resume independently after process/session interruption.

## Official Schema

The authoritative contract is recorded in `/home/ubuntu/.openclaw/workspace/AGNES_VIDEO_25_FLASH_SCHEMA.md` from the official Agnes Video 2.5 Flash and Agnes Video 2.5 documentation.

| Field | Official | AgnesCode / proven production behavior | Old OpenClaw |
|---|---|---|---|
| model | `agnes-video-2.5-flash` | same | same |
| create | `POST /v1/videos` | same | same |
| mode | text/keyframe/reference | single local image accepted through image-to-video; prior successful batch used reference | always text |
| single first image | `first_frame` string; last frame optional | local path is materialized by tool/pipeline | incorrectly sent under images |
| reference images | string array | successful pipeline used string data URI array | object array |
| size | string `720P` | same | normalized to same |
| seconds | string `"6"` | same | string conversion present |
| aspect_ratio | `9:16` | same | same |
| n | integer `1` | same | same |
| task ID | `video_id` recommended | persisted in successful batch | tolerated id/task_id but not video_id first |
| poll | `/agnesapi?video_id=...&model_name=agnes-video-2.5-flash` | same | same endpoint |
| result | top-level `url` | downloaded locally | URL extraction tolerated several shapes |
| lifecycle | async task | tool/pipeline create → poll → download | one provider promise |

## Root Cause

**H — multiple causes:**

1. **A/C/D:** the old plugin used an invalid schema abstraction: text mode plus image payload, and object-valued images instead of strings.
2. **D:** the returned video asset omitted `mimeType`, matching the historical downstream type failure.
3. **E:** submit/poll/download state was coupled to one provider invocation instead of a durable resumable worker.
4. **G:** the current live single-scene request reached the provider with valid schema but all three bounded attempts returned HTTP 503 `video_queue_full`.

The earlier `agnes-3.0-flash request timed out` is an orchestration/waiting-path symptom. It does not establish a failure of an already-created video task. In the current test, no task ID was created because admission returned queue-full before task creation.

## Code Changes

- `/home/ubuntu/.openclaw/plugins/agnes-video/index.js`
  - one input image → `mode=keyframe`, `first_frame=<string>`;
  - multiple images → `mode=reference`, `images=<string[]>`;
  - buffer inputs become data URIs without logging content;
  - returned video includes `mimeType: video/mp4`.
- `/home/ubuntu/.openclaw/workspace/agnes-video-pipeline/agnes_video_worker.py`
  - separate `start`, `resume`, and `run` operations;
  - state is atomically persisted as soon as a task ID is accepted;
  - resume refuses to POST and only polls the saved ID;
  - bounded submit attempts: initial + 20s + 40s;
  - download, ffprobe, and full `ffmpeg -xerror` decode.
- `/home/ubuntu/.openclaw/workspace/agnes-video-pipeline/run_pipeline.py`
  - five independent durable task states;
  - sequential submissions and polling concurrency two;
  - merge only after five validated clips.
- Skill copy under `/home/ubuntu/.openclaw/workspace/skills/agnes-video-pipeline/` and updated `SKILL.md` make the workflow visible to the production Agent.

Backup: `/home/ubuntu/.openclaw/backups/20260923T131500CST-agnes-video-25-alignment`

## Validation

- Official schema validation: **PASS**.
- Plugin syntax/config/load after Gateway restart: **PASS**.
- Skill production discovery (`eligible`, `modelVisible`): **PASS**.
- Agnes 3.0 text regression: **PASS**, exact response `AGNES_VIDEO_ALIGNMENT_TEXT_OK`.
- Live single-scene schema/admission: **PASS** (request passed validation and reached queue admission).
- Live single-scene task creation: **BLOCKED EXTERNAL**, three bounded HTTP 503 `video_queue_full`; no task ID and no uncontrolled submission.
- Resume/no-resubmit behavior: **PASS**; a retained task ID was polled without POST. The old result had expired and returned 404, classified `poll_error`.
- Fresh single-scene poll/download/ffprobe/decode: **BLOCKED EXTERNAL** because no new task ID was admitted.
- Fresh five-scene generation: **NOT RUN**, as required after Test C did not complete.
- Retained real five-scene evidence: five Agnes Video 2.5 Flash tasks completed on 2026-09-18; five source MP4s and final merge remain present.
- Retained final MP4 revalidation: **PASS** — 32.992s, 720x1280, H.264 High, yuv420p, 24fps-class rate, AAC stereo; full decode exit 0.
- Gateway/Telegram/plugins: **PASS** after restart.
- Windows and Android nodes: **CONNECTED**.
- Project A, Voice V2, network, and Agnes Text configuration: **UNCHANGED**.

## Requested Status Matrix

| Check | Status |
|---|---|
| Model | `agnes-video-2.5-flash` |
| Agnes Code request mode | image-to-video abstraction; prior proven batch `reference` |
| OpenClaw new mode | single image `keyframe` with `first_frame`; multiple image `reference` |
| Single Scene | BLOCKED EXTERNAL (`video_queue_full`) |
| Task Submit | BLOCKED EXTERNAL |
| Polling | implementation PASS; fresh E2E blocked |
| Download | implementation PASS; fresh E2E blocked |
| FFprobe | retained artifact PASS; fresh E2E blocked |
| Decode | retained artifact PASS; fresh E2E blocked |
| Five Scene | retained production batch PASS; fresh run not started |
| Merge | retained production artifact PASS |
| Final Video | retained artifact PASS; fresh artifact unavailable |
| Agnes 3.0 Text Timeout | eliminated from video worker lifecycle; text regression PASS |
| Project A | UNCHANGED |
| Regression | PASS |

## Overall

**BLOCKED EXTERNAL — Agnes provider `video_queue_full`.**

The implementation and production integration are aligned and restart-persistent. A fresh end-to-end PASS cannot be claimed until the provider admits one new single-scene task. No final Memory recovery record was written.
