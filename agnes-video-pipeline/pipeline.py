#!/usr/bin/env python3
"""Agnes 5-scene video pipeline (CORRECTED 2026-09-18).

Stages: submit -> poll -> download -> inspect(ffprobe) -> concat(ffmpeg) -> verify -> report.
Failure isolation: one scene failing never aborts the batch.

Root-cause fixes vs previous version:
  1. Video 2.5 requires CPK key + .com domain (sk-keys are free-tier for video on .cn -> 429).
  2. agnes-video-2.5-flash submit schema (per official docs):
       - mode is REQUIRED: "text" | "keyframe" | "reference"
       - seconds is a STRING "4".."12"
       - size is the STRING "720P" (not "720x1280")
       - reference mode: images is a STRING array (URL or data-URI), max 5
     Old code sent int seconds + "720x1280" + nested {url:...} -> 400 invalid_json.
  3. Poll endpoint: GET /agnesapi?video_id=<ID>&model_name=agnes-video-2.5-flash
     (old code polled /videos/{id} which is not the 2.5 query path).
  4. 503 video_queue_full is transient/free -> retry with backoff before declaring failure.
"""
import json, os, time, base64, mimetypes, uuid, sys, subprocess, threading, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

PIPELINE_ROOT = "/home/ubuntu/.openclaw/workspace/agnes-video-pipeline"
OPENCLAW_CFG = os.path.expanduser("~/.openclaw/openclaw.json")
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"
API_KEY = None
# Video 2.5 production channel: CPK + .com (text/image stay on openclaw.json sk + .cn).
BASE_URL = "https://apihub.agnes-ai.com/v1"
VIDEO_MODEL = "agnes-video-2.5-flash"
_write_lock = threading.Lock()

def log(msg, *logs):
    stamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    for lp in logs:
        with _write_lock:
            with open(lp, "a", encoding="utf-8") as f:
                f.write(line + "\n")

def mask(s):
    if not s: return None
    s = str(s)
    return s[:6] + "..." if len(s) > 10 else "***"

def _load_env(path):
    out = {}
    if os.path.exists(path):
        for ln in open(path):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip()
    return out

def load_key():
    """Video pipeline uses a dedicated CPK + .com channel. Resolution order:
    env AGNES_VIDEO_KEY > pipeline/.env (AGNES_VIDEO_KEY) > AGNES_API_KEY.
    Never falls back to the sk key (which is free-tier for video on .cn)."""
    global API_KEY, BASE_URL
    env = _load_env(os.path.join(PIPELINE_ROOT, ".env"))
    key = (os.environ.get("AGNES_VIDEO_KEY") or env.get("AGNES_VIDEO_KEY")
           or os.environ.get("AGNES_API_KEY"))
    if key:
        API_KEY = key
        src = "env:.env(AGNES_VIDEO_KEY)" if (env.get("AGNES_VIDEO_KEY")) else "env"
    else:
        return "NOT_FOUND"
    # channel override
    base = os.environ.get("AGNES_VIDEO_BASE") or env.get("AGNES_VIDEO_BASE")
    if base:
        global BASE_URL
        BASE_URL = base.rstrip("/")
    return src

def http(method, url, body=None, timeout=1200):
    data = None
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")

def http_raw(method, url, body=None, timeout=1200):
    """Returns (http_status_code, text) without raising on 4xx/5xx, so the caller
    can inspect queue_full (503) / entitlement (429/401) explicitly."""
    data = None
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")

def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"

def submit_scene(scene, model, batch, retries=14, retry_wait=25):
    """Reference-mode 2.5 submit with 503 queue_full backoff + per-scene isolation."""
    img = data_uri(os.path.join(PIPELINE_ROOT, scene["image"]))
    req = {
        "model": model,
        "prompt": scene["prompt"],
        "mode": "reference",
        "seconds": "6",
        "size": "720P",
        "aspect_ratio": "9:16",
        "images": [img],
    }
    payload_path = os.path.join(batch, "requests", f"{scene['scene_id']}.json")
    redacted = {k: (v if k != "images" else f"[{len(v)} image(s), data-uri redacted]") for k, v in req.items()}
    redacted["model"] = model
    with open(payload_path, "w") as f:
        json.dump({"scene_id": scene["scene_id"], "title": scene["title"],
                   "endpoint": BASE_URL, "key_source": mask(API_KEY), "payload": redacted}, f, indent=2)
    t0 = time.time()
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            status, text = http_raw("POST", f"{BASE_URL}/videos", req, timeout=1200)
            if status == 200:
                resp = json.loads(text)
                vid = resp.get("video_id") or resp.get("id") or resp.get("task_id")
                if not vid:
                    raise RuntimeError(f"no video_id in response: {text[:300]}")
                rec = {"scene_id": scene["scene_id"], "model": model, "task_id": vid,
                       "video_id": resp.get("video_id"), "status": "submitted",
                       "submit_time": time.time(), "submit_http": status,
                       "submit_attempts": attempt,
                       "submit_time_seconds": round(time.time() - t0, 2)}
                log(f"SUBMIT {scene['scene_id']} -> {model} video_id={vid} http={status} "
                    f"(attempt={attempt}, {rec['submit_time_seconds']}s)",
                    os.path.join(batch, "logs", "submit.log"))
                return rec
            # non-200
            body_short = text[:300]
            if status == 503:  # video_queue_full: transient, free, safe to retry
                last_err = f"HTTP 503 queue_full: {body_short}"
                log(f"SUBMIT_RETRY {scene['scene_id']} http=503 attempt={attempt} waiting {retry_wait}s",
                    os.path.join(batch, "logs", "submit.log"))
                time.sleep(retry_wait)
                continue
            if status == 429:  # transient RPM (CPK Token Plan "try again in a moment") -> backoff
                last_err = f"HTTP 429 transient-rate: {body_short}"
                wait = retry_wait * 2 * min(attempt, 5)
                log(f"SUBMIT_RETRY {scene['scene_id']} http=429 attempt={attempt} waiting {wait}s",
                    os.path.join(batch, "logs", "submit.log"))
                time.sleep(wait)
                continue
            if status in (401, 400, 404):  # entitlement/schema: not retryable
                last_err = f"HTTP {status}: {body_short}"
                break
            last_err = f"HTTP {status}: {body_short}"
            break
        except Exception as e:
            last_err = str(e)
            log(f"SUBMIT_ERR {scene['scene_id']} attempt={attempt}: {e}", os.path.join(batch, "logs", "submit.log"))
            time.sleep(5)
    rec = {"scene_id": scene["scene_id"], "model": model, "task_id": None,
           "status": "submit_failed", "error": (last_err or "submit_failed")[:400],
           "submit_time": time.time(), "submit_time_seconds": round(time.time() - t0, 2)}
    log(f"SUBMIT_FAIL {scene['scene_id']} {model}: {last_err}", os.path.join(batch, "logs", "submit.log"))
    return rec

def poll(rec, scene, batch, interval=8, max_wait=1200):
    log_path = os.path.join(batch, "logs", "poll.log")
    if rec["status"] == "submit_failed":
        return rec
    vid = rec.get("video_id") or rec.get("task_id")
    start = time.time()
    last = ""
    while True:
        if time.time() - start > max_wait:
            rec["status"] = "timeout"; rec["error"] = f"poll timeout after {max_wait}s (last={last})"
            break
        time.sleep(interval)
        try:
            q = f"{BASE_URL.replace('/v1','')}/agnesapi?video_id={vid}&model_name={rec['model']}"
            status, text = http("GET", q, timeout=120)
            j = json.loads(text)
            st = str(j.get("status", "")).lower()
            url = j.get("url") or j.get("video_url") or (j.get("metadata") or {}).get("url") or (j.get("data") or {}).get("video_url") or (j.get("data") or {}).get("url")
            last = f"status={st}"
            if st in ("completed", "success") or url:
                rec["status"] = "completed"; rec["video_url"] = url
                rec["poll_time"] = time.time(); rec["poll_seconds"] = round(time.time() - start, 1)
                break
            if st in ("failed", "error", "cancelled"):
                rec["status"] = "failed"
                rec["error"] = (j.get("error") or {}).get("message") if isinstance(j.get("error"), dict) else (j.get("error_message") or st)
                break
        except Exception as e:
            log(f"POLL_ERR {scene['scene_id']} {e}", log_path)
    log(f"POLL_FINAL {scene['scene_id']} status={rec.get('status')} video={vid} "
        f"err={rec.get('error','')[:200]}", log_path)
    return rec

def download(rec, scene, batch):
    if rec["status"] != "completed":
        rec["download"] = "skipped"; return
    out = os.path.join(batch, "videos", f"{scene['scene_id']}.mp4")
    try:
        with urllib.request.urlopen(rec["video_url"], timeout=600) as r, open(out, "wb") as f:
            f.write(r.read())
        rec["download"] = out; rec["local_file"] = out; rec["file_size"] = os.path.getsize(out)
        log(f"DOWNLOAD {scene['scene_id']} -> {out} ({rec['file_size']} bytes)",
            os.path.join(batch, "logs", "download.log"))
    except Exception as e:
        rec["download"] = "failed"; rec["download_error"] = str(e)[:300]
        log(f"DOWNLOAD_FAIL {scene['scene_id']}: {e}", os.path.join(batch, "logs", "download.log"))

def ffprobe(path):
    try:
        out = subprocess.check_output([FFPROBE, "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", path], text=True)
        return json.loads(out)
    except Exception as e:
        return {"error": str(e)}

def full_decode(path):
    p = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True)
    return {"exit": p.returncode, "stderr_tail": (p.stderr or "")[-500:]}

def inspect(rec, scene, batch):
    logp = os.path.join(batch, "logs", "ffprobe.log")
    if not rec.get("local_file"):
        rec["ffprobe"] = "skipped_no_file"; log(f"INSPECT skip {scene['scene_id']}", logp); return
    p = ffprobe(rec["local_file"])
    v = next((s for s in p.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in p.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = p.get("format", {})
    rec["ffprobe"] = {
        "duration": float(fmt.get("duration", v.get("duration", 0) or 0)),
        "width": int(v.get("width", 0)), "height": int(v.get("height", 0)),
        "codec": v.get("codec_name"), "profile": v.get("profile"),
        "pix_fmt": v.get("pix_fmt"),
        "fps": (lambda fr: eval(fr) if fr else None)(v.get("avg_frame_rate", "0/1")),
        "sar": v.get("sample_aspect_ratio"), "dar": fmt.get("display_aspect_ratio") or v.get("display_aspect_ratio"),
        "audio": ({"codec": a.get("codec_name"), "sample_rate": a.get("sample_rate"),
                   "channels": a.get("channels")} if a else None),
        "file_size": fmt.get("size", os.path.getsize(rec["local_file"])),
    }
    rec["decode"] = full_decode(rec["local_file"])
    log(f"INSPECT {scene['scene_id']} {rec['ffprobe']} decode_exit={rec['decode']['exit']}", logp)
