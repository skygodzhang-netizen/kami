#!/usr/bin/env python3
"""Agnes 5-scene video pipeline.

Stages: submit -> poll -> download -> inspect(ffprobe) -> concat(ffmpeg) -> verify -> report.
Failure isolation: one scene failing never aborts the batch.
Security: API key is read from OpenClaw config at runtime and is never written to
logs, manifests, or reports.
"""
import json, os, time, base64, mimetypes, uuid, sys, subprocess, threading, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

PIPELINE_ROOT = "/home/ubuntu/.openclaw/workspace/agnes-video-pipeline"
OPENCLAW_CFG = os.path.expanduser("~/.openclaw/openclaw.json")
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"
API_KEY = None
BASE_URL = "https://apihub.agnes-ai.cn/v1"
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

def load_key():
    global API_KEY
    for cand in (os.environ.get("AGNES_API_KEY"),):
        if cand:
            API_KEY = cand; return "env"
    try:
        cfg = json.load(open(OPENCLAW_CFG))
        k = cfg["models"]["providers"]["agnes"].get("apiKey")
        if k:
            API_KEY = k; return "openclaw.json"
    except Exception as e:
        print("cfg read err", e)
    return "NOT_FOUND"

def http(method, url, body=None, timeout=1200):
    data = None
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")

def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"

def submit_scene(scene, model, batch):
    req = {
        "model": model, "prompt": scene["prompt"],
        "seconds": 6, "size": "720x1280", "aspect_ratio": "9:16", "resolution": "720P",
        "images": [{"url": data_uri(os.path.join(PIPELINE_ROOT, scene["image"]))}],
    }
    payload_path = os.path.join(batch, "requests", f"{scene['scene_id']}.json")
    redacted = {k: (v if k != "images" else f"[{len(v)} image(s), data-uri redacted]") for k, v in req.items()}
    redacted["model"] = model
    with open(payload_path, "w") as f:
        json.dump({"scene_id": scene["scene_id"], "title": scene["title"], "payload": redacted}, f, indent=2)
    t0 = time.time()
    try:
        status, text = http("POST", f"{BASE_URL}/videos", req, timeout=1200)
        resp = json.loads(text)
        vid = resp.get("id") or resp.get("task_id") or (resp.get("data") or {}).get("id") or (resp.get("data") or {}).get("task_id")
        if not vid:
            raise RuntimeError(f"no video id in response: {text[:300]}")
        rec = {"scene_id": scene["scene_id"], "model": model, "task_id": vid,
               "status": "submitted", "submit_time": time.time(), "submit_http": status,
               "submit_time_seconds": round(time.time()-t0, 2)}
        log(f"SUBMIT {scene['scene_id']} -> {model} task_id={vid} http={status} ({rec['submit_time_seconds']}s)",
            os.path.join(batch, "logs", "submit.log"))
        return rec
    except Exception as e:
        rec = {"scene_id": scene["scene_id"], "model": model, "task_id": None,
               "status": "submit_failed", "error": str(e)[:400], "submit_time": time.time(),
               "submit_time_seconds": round(time.time()-t0, 2)}
        log(f"SUBMIT_FAIL {scene['scene_id']} {model}: {e}", os.path.join(batch, "logs", "submit.log"))
        return rec

def poll(rec, scene, batch, interval=5, max_wait=900):
    log_path = os.path.join(batch, "logs", "poll.log")
    if rec["status"] == "submit_failed":
        # try fallback model once
        if rec.get("model") == "agnes-video-2.5-flash":
            log(f"FALLBACK {scene['scene_id']} retry with agnes-video-v2.0", log_path)
            rec2 = submit_scene(scene, "agnes-video-v2.0", batch)
            if rec2["status"] == "submitted":
                rec.update(rec2); rec["model"] = "agnes-video-v2.0"; rec["fallback_used"] = True
            else:
                rec["error"] = (rec.get("error","") + " | fallback: " + rec2.get("error",""))[:600]
                return rec
        else:
            return rec
    start = time.time()
    last = ""
    while True:
        if time.time() - start > max_wait:
            rec["status"] = "timeout"; rec["error"] = f"poll timeout after {max_wait}s (last={last})"
            break
        time.sleep(interval)
        try:
            status, text = http("GET", f"{BASE_URL}/videos/{rec['task_id']}", timeout=120)
            j = json.loads(text)
            st = str(j.get("status", "")).lower()
            url = j.get("video_url") or j.get("url") or (j.get("data") or {}).get("video_url") or (j.get("data") or {}).get("url")
            last = f"status={st or j}"
            if st in ("completed", "success") or url:
                rec["status"] = "completed"; rec["video_url"] = url
                rec["poll_time"] = time.time(); rec["poll_seconds"] = round(time.time()-start, 1)
                break
            if st in ("failed", "error", "cancelled"):
                rec["status"] = "failed"
                rec["error"] = (j.get("error") or {}).get("message") or j.get("message") or st
                break
        except Exception as e:
            log(f"POLL_ERR {scene['scene_id']} {e}", log_path)
    if "video_url" not in rec:
        log_path2 = log_path
        log(f"POLL_FINAL {scene['scene_id']} status={rec.get('status')} task={rec['task_id']} err={rec.get('error','')[:200]}", log_path2)
    return rec

def download(rec, scene, batch):
    if rec["status"] != "completed":
        rec["download"] = "skipped"; return
    out = os.path.join(batch, "videos", f"{scene['scene_id']}.mp4")
    try:
        with urllib.request.urlopen(rec["video_url"], timeout=600) as r, open(out, "wb") as f:
            f.write(r.read())
        rec["download"] = out; rec["local_file"] = out; rec["file_size"] = os.path.getsize(out)
        log(f"DOWNLOAD {scene['scene_id']} -> {out} ({rec['file_size']} bytes)", os.path.join(batch, "logs", "download.log"))
    except Exception as e:
        rec["download"] = "failed"; rec.setdefault("error", "")["dl"] = str(e)
        rec["download_error"] = str(e)[:300]
        log(f"DOWNLOAD_FAIL {scene['scene_id']}: {e}", os.path.join(batch, "logs", "download.log"))

def ffprobe(path):
    try:
        out = subprocess.check_output([FFPROBE, "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", path], text=True)
        return json.loads(out)
    except Exception as e:
        return {"error": str(e)}

def inspect(rec, scene, batch):
    logp = os.path.join(batch, "logs", "ffprobe.log")
    if rec.get("download") != rec.get("local_file") and not rec.get("local_file"):
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
    log(f"INSPECT {scene['scene_id']} {rec['ffprobe']}", logp)
