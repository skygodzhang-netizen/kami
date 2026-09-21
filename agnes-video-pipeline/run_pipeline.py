#!/usr/bin/env python3
import json, os, time, sys, threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from pipeline import log, submit_scene, poll, download, inspect, load_key, BASE_URL, PIPELINE_ROOT
from pipeline_concat import concat, verify, write_report

def main():
    t_start = datetime.now(timezone.utc).isoformat()
    batch_id = "video-batches-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    batch = os.path.join(PIPELINE_ROOT, "runtime", batch_id)
    for d in ["input","requests","tasks","videos","logs","reports","final"]:
        os.makedirs(os.path.join(batch, d), exist_ok=True)

    cfg = json.load(open(os.path.join(PIPELINE_ROOT, "scenes.json")))
    scenes = cfg["scenes"]
    key_source = load_key()
    log(f"### Agnes 5-scene pipeline batch={batch_id} key_source={key_source} model_primary={cfg['global']['model_primary']} base={BASE_URL}",
        os.path.join(batch, "logs", "pipeline.log"))
    if key_source == "NOT_FOUND":
        log("ABORT: no Agnes API key resolvable (openclaw.json/env).", os.path.join(batch, "logs", "pipeline.log"))
        sys.exit(2)

    model_primary = cfg["global"]["model_primary"]
    reps = []
    lock = threading.Lock()

    def post_submit(rec, scene, batch):
        rec = poll(rec, scene, batch, interval=5, max_wait=900)
        download(rec, scene, batch)
        inspect(rec, scene, batch)
        return rec

    def one(scene, model):
        rec = submit_scene(scene, model, batch)
        rec = poll(rec, scene, batch, interval=5, max_wait=900)
        download(rec, scene, batch)
        inspect(rec, scene, batch)
        with lock:
            reps.append(rec)
        return rec

    # submit sequentially (avoid instant RPM burst), then poll/download/inspect in parallel
    submitted = []
    for s in scenes:
        rec = submit_scene(s, model_primary, batch)
        submitted.append(rec)
        time.sleep(8)
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(post_submit, rec, s, batch) for rec, s in zip(submitted, scenes)]
        for f in futs:
            try:
                reps.append(f.result())
            except Exception as e:
                log(f"SCENE_WORKER_EXCEPTION: {e}", os.path.join(batch, "logs", "pipeline.log"))

    # manifest (task state, evidence retained even on failure)
    manifest = {
        "batch_id": batch_id, "started_at": t_start, "model_primary": model_primary,
        "endpoint": BASE_URL,
        "tasks": [
            {"scene_id": r["scene_id"], "task_id": r.get("task_id"), "status": r.get("status"),
             "model": r.get("model"), "submit_time_seconds": r.get("submit_time_seconds"),
             "poll_seconds": r.get("poll_seconds"), "fallback_used": r.get("fallback_used"),
             "file_size": r.get("file_size"), "error": (r.get("error","")[:400] if r.get("error") else None)}
            for r in reps
        ],
    }
    with open(os.path.join(batch, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    ok_reps = [r for r in reps if r.get("local_file") and os.path.exists(r.get("local_file")) and os.path.getsize(r["local_file"]) > 0]
    log(f"### generation done: {len(ok_reps)}/{len(reps)} clips ready", os.path.join(batch, "logs", "pipeline.log"))

    concat_res = concat(reps, scenes, batch, target_w=720, target_h=1280, fps=24)
    final_out = os.path.join(batch, "final", "black_clothing_5scene_final.mp4")
    verify_res = verify(final_out, 5)

    # keep a stable copy at pipeline root final/ too
    os.makedirs(os.path.join(PIPELINE_ROOT, "final"), exist_ok=True)
    stable = os.path.join(PIPELINE_ROOT, "final", "black_clothing_5scene_final.mp4")
    import shutil
    if verify_res.get("exists"):
        shutil.copyfile(final_out, stable)

    report = write_report(batch, reps, scenes, concat_res, verify_res, key_source,
                          manifest_extra={"batch_id": batch_id, "started_at": t_start, "model": model_primary})

    # markdown report
    md = [
        "# AGNES 5-SCENE VIDEO PIPELINE — PRODUCTION VERIFICATION REPORT",
        f"\n- Batch: {batch_id}\n- Start: {t_start}\n- End: {report['ended_at']}",
        f"- OpenClaw {report['openclaw_version']} · Node {report['node_version']} · Python {report['python_version']} · FFmpeg {report['ffmpeg_version']}",
        f"- Endpoint: {report['agnes_endpoint']} · Key: source={report['key_source']} masked={report['key_masked']}",
        f"- Model: {report['model']}",
        "\n## Scene Results\n",
        "| Scene | Task | Status | Duration(s) | Res | Codec | FPS | File |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in report["scenes"]:
        fp = r.get("ffprobe") or {}
        md.append(f"| {r['scene_id']} | {str(r['task_id'])[:12]}… | {r['status']} | {fp.get('duration')} | {fp.get('width')}x{fp.get('height')} | {fp.get('codec')} | {fp.get('fps')} | {r['local_file']} |")
        if r.get("error"):
            md.append(f"| _err({r['scene_id']})_ | | | | | | | {r['error']} |")
    md += [
        "\n## Failure Isolation",
        f"- Any single-scene failure does NOT abort the batch; all 5 tasks are submitted/poll/downloaded independently.",
        f"- Clips ready: {len(ok_reps)}/{len(reps)}.",
        "\n## FFmpeg Concat",
        f"- method: {concat_res.get('method')}",
        f"- 704->720 normalization: {'scale' if concat_res.get('method')=='re-encode' else 'stream-copy'}.",
        f"- target: 720x1280 9:16 H.264 yuv420p 24fps.",
        "\n## Final File",
        f"- {report['final_file']}",
        f"- duration: {verify_res.get('duration')}s, res: {verify_res.get('width')}x{verify_res.get('height')}, DAR: {verify_res.get('dar')}, "
        f"codec: {verify_res.get('codec')} ({verify_res.get('profile')}), pix_fmt: {verify_res.get('pix_fmt')}, fps: {verify_res.get('fps')}, audio: {verify_res.get('audio')}",
        "\n## Decode Verification",
        f"- PASS: {verify_res.get('decode_ok')} · errors: {verify_res.get('decode_errors')}",
        "\n## Scene Boundaries (I-frame pts, s)",
        f"- {verify_res.get('keyframe_times')}",
        "\n## Artifacts",
        f"- batch dir: {batch}",
        f"- source videos: {batch}/videos/*.mp4 (retained)",
        f"- logs: {batch}/logs/ · manifest: {batch}/manifest.json · report: {batch}/reports/production-report.json",
        "\n## Security",
        f"- API key NOT written to logs/manifest/report; shown only as masked prefix {report['key_masked']}.",
    ]
    with open(os.path.join(batch, "reports", "production-report.md"), "w") as f:
        f.write("\n".join(md))

    print(json.dumps({"batch": batch, "ok_clips": len(ok_reps), "total": len(reps),
                      "concat_method": concat_res.get("method"), "verify_pass": verify_res.get("pass"),
                      "final": report["final_file"]}, indent=2))

if __name__ == "__main__":
    main()
