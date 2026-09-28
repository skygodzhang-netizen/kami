#!/usr/bin/env python3
"""Unified, durable Agnes Video production worker.

Production route is intentionally fixed to apihub.agnes-ai.com + AGNES_VIDEO_KEY.
The worker writes a recoverable manifest before any network request and never
re-submits after an ambiguous transport failure.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/ubuntu/.openclaw/workspace/agnes-video-pipeline")
ENV_FILE = ROOT / ".env"
RUNTIME = ROOT / "runtime" / "unified-video-jobs"
BASE_URL = "https://apihub.agnes-ai.com/v1"
PRIMARY_MODEL = "agnes-video-2.5-flash"
FALLBACK_MODEL = "agnes-video-v2.0"
MODEL = PRIMARY_MODEL  # backward compatibility for run_pipeline.py
VALID_MODES = {"text", "keyframe", "reference"}
VALID_ASPECTS = {"21:9", "16:9", "4:3", "1:1", "3:4", "9:16"}
VALID_SECONDS = {str(x) for x in range(4, 13)}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".opus", ".flac"}
REFERENCE_IMAGE_LIMIT = 5
SUBMIT_DELAYS = (20, 40)
POLL_INTERVAL = 8
POLL_DEADLINE = 1800
MIN_VIDEO_BYTES = 16 * 1024


class WorkerError(RuntimeError):
    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    json.loads(tmp.read_text(encoding="utf-8"))
    os.replace(tmp, path)
    fsync_dir(path.parent)


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_config() -> tuple[str, str]:
    values = load_env(ENV_FILE)
    key = os.environ.get("AGNES_VIDEO_KEY") or values.get("AGNES_VIDEO_KEY")
    configured_base = os.environ.get("AGNES_VIDEO_BASE") or values.get("AGNES_VIDEO_BASE") or BASE_URL
    base = configured_base.rstrip("/")
    if not key:
        raise WorkerError("AUTH_ERROR", "AGNES_VIDEO_KEY is not configured")
    if not key.lower().startswith("cpk"):
        raise WorkerError("AUTH_ERROR", "AGNES_VIDEO_KEY is not a CPK credential")
    if base != BASE_URL:
        raise WorkerError("AUTH_ERROR", f"video production endpoint must be {BASE_URL}")
    return key, base


def key_fingerprint(key: str) -> dict:
    return {"prefix": key[:3], "suffix": key[-4:], "length": len(key), "sha256_16": hashlib.sha256(key.encode()).hexdigest()[:16]}


def classify_http(code: int, payload: dict) -> str:
    text = detail(payload).lower()
    normalized = re.sub(r"[^a-z0-9]+", "", text)
    if code in (401, 403): return "AUTH_ERROR"
    if code == 503 and ("videoqueuefull" in normalized or "videoqueueisfull" in normalized or "queuefull" in normalized): return "QUEUE_FULL"
    if code == 429: return "RATE_LIMIT"
    if code == 400: return "BAD_REQUEST"
    if code == 0: return "NETWORK_ERROR"
    if code >= 500: return "NETWORK_ERROR"
    return "UNKNOWN_ERROR"


def request_json(method: str, url: str, key: str, body: dict | None = None, timeout: int = 180) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", "replace")
            try: return response.status, json.loads(raw)
            except json.JSONDecodeError: return response.status, {"message": raw[:500]}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try: payload = json.loads(raw)
        except json.JSONDecodeError: payload = {"message": raw[:500]}
        return exc.code, payload
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
        return 0, {"error": "network_error", "message": str(exc)[:500]}


def task_id(payload: dict) -> str | None:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    return payload.get("video_id") or payload.get("task_id") or payload.get("id") or data.get("video_id") or data.get("task_id") or data.get("id")


def detail(payload: object) -> str:
    if not isinstance(payload, dict): return str(payload)[:500]
    value = payload.get("detail") or payload.get("message") or payload.get("error")
    if isinstance(value, dict): value = value.get("code") or value.get("message") or json.dumps(value)
    return str(value or payload)[:500]


def validate_local_media(value: str, kind: str) -> Path:
    if value == "/dev/null": raise WorkerError("INVALID_INPUT", "/dev/null is forbidden")
    if value.startswith("https://"):
        return Path(value)  # URL input is validated by scheme; provider fetches it.
    path = Path(value).expanduser().resolve()
    if not path.is_file() or path.stat().st_size <= 0:
        raise WorkerError("INVALID_INPUT", f"{kind} file does not exist or is empty: {path}")
    allowed = IMAGE_EXTENSIONS if kind == "image" else AUDIO_EXTENSIONS
    if path.suffix.lower() not in allowed:
        raise WorkerError("INVALID_INPUT", f"unsupported {kind} extension: {path.suffix}")
    if kind == "image":
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_type,width,height", "-of", "json", str(path)], capture_output=True, text=True)
        if probe.returncode != 0:
            raise WorkerError("INVALID_INPUT", f"image is not decodable: {path}")
        try: streams = json.loads(probe.stdout).get("streams", [])
        except json.JSONDecodeError: streams = []
        if not streams or not streams[0].get("width") or not streams[0].get("height"):
            raise WorkerError("INVALID_INPUT", f"image has no decodable video stream: {path}")
    else:
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type,duration", "-of", "json", str(path)], capture_output=True, text=True)
        if probe.returncode != 0:
            raise WorkerError("INVALID_INPUT", f"audio is not decodable: {path}")
    return path


def media_value(value: str, kind: str) -> tuple[str, str]:
    validated = validate_local_media(value, kind)
    if value.startswith("https://"): return value, "https"
    mime = mimetypes.guess_type(validated.name)[0] or ("image/jpeg" if kind == "image" else "audio/mpeg")
    return f"data:{mime};base64,{base64.b64encode(validated.read_bytes()).decode()}", "data-uri"


def determine_mode(prompt: str, explicit: str | None, first_frame: str | None, last_frame: str | None,
                   reference_images: list[str], reference_audios: list[str]) -> str:
    if not prompt.strip(): raise WorkerError("INVALID_INPUT", "prompt must not be empty")
    if last_frame and not first_frame: raise WorkerError("INVALID_INPUT", "last_frame requires first_frame")
    if first_frame and (reference_images or reference_audios): raise WorkerError("INVALID_INPUT", "keyframe and reference inputs cannot be mixed")
    inferred = "keyframe" if first_frame else ("reference" if reference_images or reference_audios else "text")
    if explicit and explicit not in VALID_MODES: raise WorkerError("UNSUPPORTED_MODE", f"unsupported mode: {explicit}")
    if explicit and explicit != inferred: raise WorkerError("INVALID_INPUT", f"explicit mode {explicit} conflicts with inferred mode {inferred}")
    return explicit or inferred


def validate_options(mode: str, prompt: str, first_frame: str | None, last_frame: str | None,
                     reference_images: list[str], reference_audios: list[str], size: str, seconds: str,
                     aspect_ratio: str, n: int) -> None:
    if size != "720P": raise WorkerError("INVALID_INPUT", "Agnes Video 2.5 production size must be 720P")
    if seconds not in VALID_SECONDS: raise WorkerError("INVALID_INPUT", "seconds must be a string value from 4 through 12")
    if aspect_ratio not in VALID_ASPECTS: raise WorkerError("INVALID_INPUT", f"unsupported aspect_ratio: {aspect_ratio}")
    if n != 1: raise WorkerError("INVALID_INPUT", "production worker currently supports n=1")
    if mode == "text" and (first_frame or last_frame or reference_images or reference_audios):
        raise WorkerError("INVALID_INPUT", "text mode cannot contain media")
    if mode == "keyframe" and not first_frame: raise WorkerError("INVALID_INPUT", "keyframe mode requires first_frame")
    if mode == "reference" and not (reference_images or reference_audios): raise WorkerError("INVALID_INPUT", "reference mode requires media")
    if len(reference_images) > REFERENCE_IMAGE_LIMIT: raise WorkerError("INVALID_INPUT", f"reference images exceed limit {REFERENCE_IMAGE_LIMIT}")
    if reference_audios:
        raise WorkerError("UNSUPPORTED_MODE", "audio reference is not enabled: no current Agnes schema evidence")
    if mode == "keyframe":
        validate_local_media(first_frame, "image")
        if last_frame: validate_local_media(last_frame, "image")
    for item in reference_images: validate_local_media(item, "image")


def new_manifest(job_id: str, prompt: str, mode: str, first_frame: str | None, last_frame: str | None,
                 reference_images: list[str], reference_audios: list[str], size: str, seconds: str,
                 aspect_ratio: str, n: int, output: Path) -> dict:
    return {
        "schema": 3, "worker": "unified-agnes-video-production-worker", "job_id": job_id,
        "created_at": now(), "updated_at": now(), "mode": mode, "model": PRIMARY_MODEL,
        "endpoint": BASE_URL, "prompt": prompt, "negative_prompt": None, "size": size,
        "seconds": seconds, "aspect_ratio": aspect_ratio, "n": n,
        "first_frame": first_frame, "last_frame": last_frame, "images": reference_images,
        "audios": reference_audios, "status": "pending", "error_class": None,
        "submit_attempts": 0, "primary_attempts": 0, "primary_task_id": None,
        "fallback_attempts": 0, "fallback_task_id": None, "task_id": None,
        "active_model": None, "fallback_used": False, "fallback_reason": None,
        "output_file": str(output), "downloaded": False, "ffprobe_verified": False,
        "decode_verified": False, "validation": None, "last_error": None,
    }


def build_primary_body(state: dict) -> tuple[dict, dict]:
    body = {k: state[k] for k in ("model", "mode", "prompt", "size", "seconds", "aspect_ratio", "n")}
    transports: dict[str, object] = {}
    if state["mode"] == "keyframe":
        body["first_frame"], transports["first_frame"] = media_value(state["first_frame"], "image")
        if state.get("last_frame"):
            body["last_frame"], transports["last_frame"] = media_value(state["last_frame"], "image")
    elif state["mode"] == "reference":
        body["images"] = []
        transports["images"] = []
        for item in state.get("images", []):
            value, transport = media_value(item, "image"); body["images"].append(value); transports["images"].append(transport)
    return body, transports


def fallback_body(state: dict) -> dict | None:
    mode = state["mode"]
    if mode == "reference" or state.get("last_frame"): return None
    dimensions = {"21:9": (1344, 576), "16:9": (1280, 720), "4:3": (960, 720), "1:1": (720, 720), "3:4": (720, 960), "9:16": (720, 1280)}
    width, height = dimensions[state["aspect_ratio"]]
    frames = int(state["seconds"]) * 24 + 1
    body = {"model": FALLBACK_MODEL, "prompt": state["prompt"], "width": width, "height": height, "num_frames": frames, "frame_rate": 24}
    if mode == "keyframe": body["image"] = media_value(state["first_frame"], "image")[0]
    return body


def submit_body(state_path: Path, state: dict, key: str, base: str, model: str, body: dict,
                task_field: str, attempts_field: str) -> str:
    for attempt in range(1, 4):
        state.update({"status": "submitting", attempts_field: attempt, "submit_attempts": state.get("submit_attempts", 0) + 1, "updated_at": now()})
        atomic_json(state_path, state)
        code, payload = request_json("POST", base + "/videos", key, body)
        category = classify_http(code, payload)
        task = task_id(payload)
        state.update({"last_submit_http": code, "updated_at": now()})
        if code in (200, 201, 202) and task:
            state.update({task_field: task, "task_id": task, "video_id": task, "active_model": model, "status": "submitted", "error_class": None, "last_error": None})
            atomic_json(state_path, state)
            return "accepted"
        state.update({"error_class": category, "last_error": detail(payload)})
        if category == "NETWORK_ERROR":
            state["status"] = "submit_unknown"
            atomic_json(state_path, state)
            return "unknown"
        state["status"] = "submit_failed"
        atomic_json(state_path, state)
        if category not in ("QUEUE_FULL", "RATE_LIMIT"): return "terminal"
        if attempt < 3: time.sleep(SUBMIT_DELAYS[attempt - 1])
    return "queue_full" if state.get("error_class") == "QUEUE_FULL" else "retry_exhausted"


def submit(state_path: Path, prompt: str | None = None, image: str | None = None, scene: str | None = None,
           **kwargs) -> dict:
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("task_id") or state.get("primary_task_id") or state.get("fallback_task_id"): return state
        if state.get("status") in ("submitting", "submit_unknown"):
            state.update({"status": "manual_reconciliation_required", "error_class": "NETWORK_ERROR", "last_error": "previous submit outcome is ambiguous; refusing duplicate POST"})
            atomic_json(state_path, state); return state
    if kwargs:
        mode = kwargs["mode"]
        output = Path(kwargs["output"])
        state = new_manifest(kwargs["job_id"], prompt or "", mode, kwargs.get("first_frame"), kwargs.get("last_frame"), kwargs.get("reference_images", []), kwargs.get("reference_audios", []), kwargs["size"], kwargs["seconds"], kwargs["aspect_ratio"], kwargs["n"], output)
    else:
        # Compatibility path for the proven five-scene runner.
        output = state_path.parent.parent / "videos" / f"{scene}.mp4"
        state = new_manifest(scene or state_path.stem, prompt or "", "keyframe", image, None, [], [], "720P", "6", "9:16", 1, output)
        state.update({"scene": scene, "scene_id": scene, "input_image": image, "primary_model": PRIMARY_MODEL, "fallback_model": FALLBACK_MODEL, "fallback_triggered": False})
    atomic_json(state_path, state)
    key, base = load_config()
    body, transports = build_primary_body(state)
    state["media_transport"] = transports
    atomic_json(state_path, state)
    outcome = submit_body(state_path, state, key, base, PRIMARY_MODEL, body, "primary_task_id", "primary_attempts")
    if outcome == "accepted": return state
    if outcome != "queue_full": return state
    fb = fallback_body(state)
    if fb is None:
        state.update({"status": "submit_failed", "fallback_used": False, "fallback_reason": "mode_not_safely_convertible", "last_error": "primary queue exhausted; fallback cannot preserve this mode"})
        atomic_json(state_path, state); return state
    state.update({"fallback_used": True, "fallback_triggered": True, "fallback_reason": "video_queue_full", "active_model": FALLBACK_MODEL, "updated_at": now()})
    atomic_json(state_path, state)
    outcome = submit_body(state_path, state, key, base, FALLBACK_MODEL, fb, "fallback_task_id", "fallback_attempts")
    if outcome != "accepted": state["status"] = "submit_failed"; atomic_json(state_path, state)
    return state


def active_task(state: dict) -> tuple[str | None, str | None]:
    if state.get("primary_task_id"): return state["primary_task_id"], PRIMARY_MODEL
    if state.get("fallback_task_id"): return state["fallback_task_id"], FALLBACK_MODEL
    if state.get("task_id"): return state["task_id"], state.get("active_model") or PRIMARY_MODEL
    if state.get("video_id"): return state["video_id"], state.get("active_model") or PRIMARY_MODEL
    return None, None


def poll_url(base: str, task: str, model: str) -> str:
    origin = urllib.parse.urlsplit(base)._replace(path="", query="", fragment="").geturl()
    return origin + "/agnesapi?" + urllib.parse.urlencode({"video_id": task, "model_name": model})


def extract_status(payload: dict) -> tuple[str, dict]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return str(data.get("status") or payload.get("status") or "").lower(), data


def verify_video(output: Path) -> dict:
    if not output.is_file() or output.stat().st_size < MIN_VIDEO_BYTES:
        raise WorkerError("VERIFY_FAILED", f"video missing or below {MIN_VIDEO_BYTES} bytes")
    try:
        probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(output)], text=True))
    except Exception as exc:
        raise WorkerError("VERIFY_FAILED", f"ffprobe failed: {exc}") from exc
    video = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in probe.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not video or not video.get("width") or not video.get("height"):
        raise WorkerError("VERIFY_FAILED", "ffprobe found no valid video stream")
    decode = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(output), "-f", "null", "-"], capture_output=True, text=True)
    if decode.returncode != 0:
        raise WorkerError("VERIFY_FAILED", (decode.stderr or "full decode failed")[:500])
    return {"bytes": output.stat().st_size, "duration": probe.get("format", {}).get("duration"), "codec": video.get("codec_name"), "width": video.get("width"), "height": video.get("height"), "pix_fmt": video.get("pix_fmt"), "fps": video.get("avg_frame_rate"), "audio_codec": audio.get("codec_name") if audio else None, "decode_exit": decode.returncode}


def poll(state_path: Path, output: Path | None = None) -> dict:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    output = output or Path(state["output_file"])
    if state.get("decode_verified") and output.exists(): return state
    if output.exists() and state.get("downloaded"):
        state["status"] = "verifying"; atomic_json(state_path, state)
        try: validation = verify_video(output)
        except WorkerError as exc: state.update({"status": "verify_failed", "error_class": exc.category, "last_error": str(exc)}); atomic_json(state_path, state); return state
        state.update({"status": "completed", "validation": validation, "bytes": validation["bytes"], "output": str(output), "output_file": str(output), "ffprobe_verified": True, "decode_verified": True, "finished_at": now(), "last_error": None, "error_class": None}); atomic_json(state_path, state); return state
    task, model = active_task(state)
    if not task: raise WorkerError("INVALID_INPUT", "state has no task_id; refusing to submit during resume")
    key, base = load_config(); deadline = time.monotonic() + POLL_DEADLINE; errors = 0
    while time.monotonic() < deadline:
        state.update({"status": "polling", "updated_at": now()}); atomic_json(state_path, state)
        code, payload = request_json("GET", poll_url(base, task, model), key, timeout=120)
        if code != 200:
            errors += 1; state.update({"error_class": classify_http(code, payload), "last_error": detail(payload), "poll_http": code}); atomic_json(state_path, state)
            if errors >= 5: state["status"] = "poll_failed"; atomic_json(state_path, state); return state
            time.sleep(min(POLL_INTERVAL * errors, 30)); continue
        errors = 0; provider_status, data = extract_status(payload)
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        result_url = metadata.get("url") or data.get("url") or data.get("video_url") or data.get("output_url")
        state.update({"provider_status": provider_status, "progress": data.get("progress"), "active_model": model, "task_id": task, "updated_at": now()}); atomic_json(state_path, state)
        if provider_status in ("failed", "error", "cancelled", "canceled"):
            state.update({"status": "task_failed", "error_class": "TASK_FAILED", "last_error": detail(payload), "finished_at": now()}); atomic_json(state_path, state); return state
        if provider_status in ("completed", "success", "succeeded") or result_url:
            if not result_url: state.update({"status": "download_failed", "error_class": "DOWNLOAD_FAILED", "last_error": "completed response missing URL"}); atomic_json(state_path, state); return state
            output.parent.mkdir(parents=True, exist_ok=True); partial = output.with_suffix(output.suffix + ".part")
            state["status"] = "downloading"; atomic_json(state_path, state)
            try:
                with urllib.request.urlopen(urllib.request.Request(result_url, headers={"Accept": "video/*"}), timeout=600) as response, partial.open("wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk: break
                        handle.write(chunk)
                    handle.flush(); os.fsync(handle.fileno())
                os.replace(partial, output); fsync_dir(output.parent)
            except Exception as exc:
                state.update({"status": "download_failed", "error_class": "DOWNLOAD_FAILED", "last_error": str(exc)[:500]}); atomic_json(state_path, state); return state
            state.update({"downloaded": True, "status": "verifying", "output_file": str(output)}); atomic_json(state_path, state)
            return poll(state_path, output)
        time.sleep(POLL_INTERVAL)
    state.update({"status": "poll_timeout", "error_class": "NETWORK_ERROR", "last_error": "poll deadline exceeded", "finished_at": now()}); atomic_json(state_path, state); return state


def resume_runtime(path: Path) -> list[dict]:
    results = []
    for state_path in sorted(path.rglob("*.json")):
        try: state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception: continue
        if state.get("worker") != "unified-agnes-video-production-worker": continue
        if state.get("status") in ("submitted", "polling", "downloading", "verifying"):
            results.append(poll(state_path))
    return results


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified Agnes Video production worker")
    sub = parser.add_subparsers(dest="cmd", required=True)
    start = sub.add_parser("start")
    start.add_argument("--state"); start.add_argument("--output"); start.add_argument("--job-id")
    start.add_argument("--prompt", required=True); start.add_argument("--mode", choices=sorted(VALID_MODES))
    start.add_argument("--first-frame", "--image", dest="first_frame"); start.add_argument("--last-frame")
    start.add_argument("--reference-image", action="append", default=[]); start.add_argument("--reference-audio", action="append", default=[])
    start.add_argument("--size", default="720P"); start.add_argument("--seconds", default="6")
    start.add_argument("--aspect-ratio", default="16:9"); start.add_argument("--n", type=int, default=1); start.add_argument("--scene")
    resume = sub.add_parser("resume"); resume.add_argument("--state"); resume.add_argument("--output"); resume.add_argument("--runtime")
    run = sub.add_parser("run")
    for action in start._actions[1:]:
        if not action.option_strings: continue
        opts = action.option_strings
        kwargs = {"dest": action.dest, "default": action.default, "required": action.required}
        if isinstance(action, argparse._AppendAction): kwargs["action"] = "append"
        elif action.type: kwargs["type"] = action.type
        elif action.choices: kwargs["choices"] = action.choices
        run.add_argument(*opts, **kwargs)
    return parser


def main() -> int:
    args = make_parser().parse_args()
    try:
        if args.cmd == "resume":
            if args.runtime:
                states = resume_runtime(Path(args.runtime)); print(json.dumps(states, ensure_ascii=False)); return 0 if all(x.get("status") == "completed" for x in states) else 2
            if not args.state: raise WorkerError("INVALID_INPUT", "resume requires --state or --runtime")
            state = poll(Path(args.state), Path(args.output) if args.output else None)
        else:
            mode = determine_mode(args.prompt, args.mode, args.first_frame, args.last_frame, args.reference_image, args.reference_audio)
            validate_options(mode, args.prompt, args.first_frame, args.last_frame, args.reference_image, args.reference_audio, args.size, str(args.seconds), args.aspect_ratio, args.n)
            job_id = args.job_id or args.scene or f"video-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
            job_dir = RUNTIME / job_id
            state_path = Path(args.state) if args.state else job_dir / "manifest.json"
            output = Path(args.output) if args.output else job_dir / "output.mp4"
            state = submit(state_path, args.prompt, args.first_frame, args.scene, mode=mode, output=output, job_id=job_id, first_frame=args.first_frame, last_frame=args.last_frame, reference_images=args.reference_image, reference_audios=args.reference_audio, size=args.size, seconds=str(args.seconds), aspect_ratio=args.aspect_ratio, n=args.n)
            if args.cmd == "run" and active_task(state)[0]: state = poll(state_path, output)
        print(json.dumps(state, ensure_ascii=False))
        return 0 if state.get("status") in ("submitted", "polling", "completed") else 2
    except WorkerError as exc:
        print(json.dumps({"status": "failed", "error_class": exc.category, "last_error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
