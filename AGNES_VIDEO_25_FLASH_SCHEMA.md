# Agnes Video 2.5 Flash API Schema

Source priority: Agnes official documentation, then observed AgnesCode behavior, then the previous OpenClaw implementation.

| Item | Confirmed contract |
|---|---|
| CREATE METHOD | `POST` |
| CREATE ENDPOINT | `/v1/videos` |
| MODEL FIELD | `model` = `agnes-video-2.5-flash` |
| PROMPT FIELD | `prompt` (string, required) |
| MODE FIELD | `mode` (string, required) |
| MODE VALUES | `text`, `keyframe`, `reference` |
| IMAGE INPUT | `first_frame`/`last_frame` strings for keyframe; `images` string array for reference |
| KEYFRAME RULE | At least one of `first_frame` or `last_frame`; a first frame alone is valid |
| SIZE | `size` string; Flash only accepts `720P` |
| SECONDS | `seconds` string in `4` through `12` |
| ASPECT RATIO | `aspect_ratio`: `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` |
| N | `n` integer; only `1` |
| CREATE RESPONSE | `video_id` is the retrieval identifier; `id` and `task_id` also identify the async task |
| POLL METHOD | `GET` |
| POLL ENDPOINT | `/agnesapi?video_id=<VIDEO_ID>&model_name=agnes-video-2.5-flash` |
| STATUS FIELD | top-level `status` |
| PENDING | queued/pending/processing/in_progress |
| SUCCESS | `completed` (also tolerate `success`) |
| FAILURE | `failed` (also tolerate error/cancelled) |
| RESULT VIDEO | top-level `url` |
| DOWNLOAD | HTTPS GET of result URL |

Official documentation says media URLs must remain publicly accessible. The current production endpoint has also accepted image data URIs in successful September 2026 jobs. The worker supports HTTPS URLs and local files encoded as data URIs, records which transport was used, and never logs the media body.

Observed AgnesCode behavior: its `agnes_aigc__image_to_video` accepts a local path, URL, or prior-generation metadata and performs create, poll, and local download outside the text model request. Server logs also show the successful workflow using the `.com` video endpoint and `/agnesapi` polling. The local AgnesCode orchestration used shell tooling for the prior five-scene production run; it did not prove a conflicting wire schema.

Previous OpenClaw plugin mismatch: it always sent `mode: text`, then added `images` as objects. That violates the official mode rules and image type. It also kept provider polling inside one generation call rather than exposing durable resumable task state.
