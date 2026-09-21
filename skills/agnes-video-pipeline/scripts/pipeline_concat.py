"""Concat + verify + report for the Agnes 5-scene pipeline.

Top-level imports: os/json/subprocess/re + shared helpers from pipeline.
Failure-isolated: 0-clip input returns a graceful result instead of crashing.
"""
import os
import json
import subprocess
import re
from datetime import datetime, timezone

from pipeline import log, ffprobe, FFMPEG, API_KEY, mask


def concat(reps, scenes, batch, target_w=720, target_h=1280, fps=24):
    """Stream-copy concat when all clips share codec/res/fps AND already target size;
    else filter re-encode to 720x1280 9:16 H.264 yuv420p 24fps (704->720 normalization)."""
    logp = os.path.join(batch, "logs", "ffmpeg.log")
    ok = [r for r in reps
          if r.get("local_file") and os.path.exists(r.get("local_file")) and os.path.getsize(r["local_file"]) > 0]
    if not ok:
        log("CONCAT: no valid clips (generation blocked)", logp)
        return {"method": "none", "error": "no clips available to concat", "count": 0}

    # Enforce strict scene order using the scenes list.
    by_scene = {}
    for s in scenes:
        for r in ok:
            if r["scene_id"] == s["scene_id"]:
                by_scene[s["scene_id"]] = r
    ordered = [by_scene[s["scene_id"]] for s in scenes if s["scene_id"] in by_scene]
    files = [r["local_file"] for r in ordered]
    out = os.path.join(batch, "final", "black_clothing_5scene_final.mp4")

    def sig(f):
        p = ffprobe(f)
        v = next((s for s in p.get("streams", []) if s.get("codec_type") == "video"), {})
        a = next((s for s in p.get("streams", []) if s.get("codec_type") == "audio"), None)
        fps_v = eval(v.get("avg_frame_rate", "0/1")) if v.get("avg_frame_rate") else None
        return {
            "codec": v.get("codec_name"), "profile": v.get("profile"), "pix_fmt": v.get("pix_fmt"),
            "w": int(v.get("width", 0)), "h": int(v.get("height", 0)), "fps": fps_v,
            "audio": a.get("codec_name") if a else None, "ar": a.get("sample_rate") if a else None,
            "ch": a.get("channels") if a else None,
        }

    sigs = [sig(f) for f in files]
    all_same = len(set(json.dumps(x, sort_keys=True) for x in sigs)) == 1
    already_target = sigs[0]["w"] == target_w and sigs[0]["h"] == target_h
    all_have_audio = all(x["audio"] for x in sigs)

    log(f"CONCAT compat={all_same} already_target={already_target} all_audio={all_have_audio} sigs={sigs}", logp)

    if all_same and already_target:
        lst = os.path.join(batch, "final", "concat_list.txt")
        with open(lst, "w") as f:
            for p in files:
                f.write(f"file '{p}'\n")
        cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst,
               "-c", "copy", "-movflags", "+faststart", out]
        method = "stream-copy"
    else:
        inp = []
        for p in files:
            inp += ["-i", p]
        n = len(files)
        filt = "".join(f"[{i}:v]scale={target_w}:{target_h}:flags=lanczos,setsar=1,fps={fps}[v{i}]" for i in range(n))
        fc = filt + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vout]"
        cmd = [FFMPEG, "-y"] + inp + [
            "-filter_complex", fc, "-map", "[vout]",
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.0",
            "-pix_fmt", "yuv420p", "-r", str(fps),
            "-movflags", "+faststart", out]
        method = "re-encode"

    log(f"CONCAT method={method} files={len(files)}", logp)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    tail = (proc.stderr or "")[-2500:]
    with open(os.path.join(batch, "logs", "ffmpeg_last.log"), "w") as f:
        f.write("RC=" + str(proc.returncode) + "\n" + tail)
    if proc.returncode != 0:
        log(f"CONCAT_FAIL: {tail[-1200:]}", logp)
        return {"method": method, "error": tail[-1500:], "rc": proc.returncode, "count": len(files),
                "compat": all_same, "sigs": sigs}
    return {"method": method, "output": out, "rc": proc.returncode, "count": len(files),
            "compat": all_same, "already_target": already_target, "all_have_audio": all_have_audio,
            "normalization": "scale" if not already_target else "stream-copy",
            "sigs": sigs}


def keyframe_times(path, fps=24):
    p = subprocess.run([FFMPEG, "-hide_banner", "-i", path, "-vf",
                        "select='eq(pict_type,I)',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True)
    return [float(m.group(1)) for m in re.finditer(r"pts_time:\s*([\d.]+)", p.stderr)]


def verify(out, expected_scenes):
    res = {"exists": os.path.exists(out), "size": os.path.getsize(out) if os.path.exists(out) else 0}
    if not res["exists"]:
        res.update(decode_ok=False, pass_=False, keyframe_times=[],
                   note="final file missing (0 clips -> no concat)")
        return res
    p = ffprobe(out)
    v = next((s for s in p.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in p.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = p.get("format", {})
    res.update({
        "duration": float(fmt.get("duration", 0)),
        "width": int(v.get("width", 0)), "height": int(v.get("height", 0)),
        "codec": v.get("codec_name"), "profile": v.get("profile"),
        "pix_fmt": v.get("pix_fmt"),
        "fps": eval(v.get("avg_frame_rate", "0/1")) if v.get("avg_frame_rate") else None,
        "dar": fmt.get("display_aspect_ratio") or v.get("display_aspect_ratio"),
        "sar": v.get("sample_aspect_ratio"),
        "audio": ({"codec": a.get("codec_name"), "sample_rate": a.get("sample_rate"), "channels": a.get("channels")} if a else None),
        "container": fmt.get("format_name"),
    })
    dc = subprocess.run([FFMPEG, "-v", "error", "-i", out, "-f", "null", "-"], capture_output=True, text=True)
    res["decode_errors"] = (dc.stderr.strip() or "none")
    res["decode_ok"] = dc.returncode == 0
    kts = keyframe_times(out, res.get("fps") or 24)
    res["keyframe_times"] = [round(k, 3) for k in kts]
    res["scene_present"] = len(kts) >= expected_scenes and all(k < 25.5 for k in kts[:expected_scenes]) if kts else False
    res["pass"] = (res["decode_ok"] and res["width"] == 720 and res["height"] == 1280
                   and res["codec"] == "h264" and res["pix_fmt"] == "yuv420p" and res["fps"] == 24
                   and abs(res["duration"] - 30) < 4 and res["scene_present"])
    return res


def write_report(batch, reps, scenes, concat_res, verify_res, key_source, manifest_extra):
    report = {
        "batch_id": manifest_extra.get("batch_id"),
        "started_at": manifest_extra.get("started_at"),
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "openclaw_version": "2026.9.4", "node_version": "v24.21.0",
        "python_version": "3.12.3", "ffmpeg_version": "6.1.1 (system)",
        "agnes_endpoint": "https://apihub.agnes-ai.cn/v1",
        "key_source": key_source, "key_present": bool(API_KEY), "key_masked": mask(API_KEY),
        "model": manifest_extra.get("model"),
        "production_verified": False,  # set by runner only if verify_res.get("pass")
        "scenes": [
            {"scene_id": r["scene_id"],
             "title": next((s["title"] for s in scenes if s["scene_id"] == r["scene_id"]), r["scene_id"]),
             "task_id": r.get("task_id"), "status": r.get("status"), "model": r.get("model"),
             "video_url": r.get("video_url"), "local_file": r.get("local_file"),
             "file_size": r.get("file_size"), "error": r.get("error"),
             "poll_seconds": r.get("poll_seconds"), "fallback_used": r.get("fallback_used"),
             "ffprobe": r.get("ffprobe")}
            for r in reps
        ],
        "concat": concat_res, "verify": verify_res,
        "final_file": os.path.join(batch, "final", "black_clothing_5scene_final.mp4"),
    }
    with open(os.path.join(batch, "reports", "production-report.json"), "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return report
