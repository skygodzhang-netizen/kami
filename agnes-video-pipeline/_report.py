import json, os, glob, datetime, subprocess

ROOT = "/home/ubuntu/.openclaw/workspace/agnes-video-pipeline"
RT = os.path.join(ROOT, "runtime")
DEMOfinal = os.path.join(RT, "downstream_demo", "downstream_demo_final.mp4")
FFP = "/usr/bin/ffprobe"

def ffprobe(p):
    if not os.path.exists(p): return None
    d = json.loads(subprocess.check_output([FFP, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", p], text=True))
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    f = d.get("format", {})
    return {"dur": float(f.get("duration", 0)), "w": v.get("width"), "h": v.get("height"),
            "codec": v.get("codec_name"), "pix": v.get("pix_fmt"), "fps": v.get("avg_frame_rate"),
            "size": f.get("size"), "audio": (a.get("codec_name") if a else None)}

# find latest 5-scene batch manifest
batches = sorted(glob.glob(os.path.join(RT, "video-batches-*")))
b = batches[-1] if batches else None
manifest = json.load(open(os.path.join(b, "manifest.json"))) if b else {"tasks": []}
salvaged = sorted(glob.glob(os.path.join(RT, "downstream_demo", "v20_txt_*.mp4")))

report = {
    "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "environment": {
        "host": "ubuntu-ai (192.168.100.108)", "os": "Ubuntu 24.04.4 LTS",
        "openclaw": "2026.9.4 (3a9d69d)", "node": "v24.21.0", "python": "3.12.3",
        "ffmpeg": "6.1.1 (/usr/bin/ffmpeg)", "ffprobe": "/usr/bin/ffprobe",
        "gateway": "openclaw-gateway.service active(running), :18789 bind=lan TLS",
        "agnes_provider": "registered (models.providers.agnes, baseUrl https://apihub.agnes-ai.cn/v1, apiKey present, source models.json)",
        "agnes_video_models": ["agnes/agnes-video-2.5-flash", "agnes/agnes-video-v2.0"],
        "mediaModel_video_primary": "agnes/agnes-video-2.5-flash",
    },
    "input": {"images": ["scene01..scene05.jpg in input/"], "prompts": "5 scene prompts (see scenes.json)"},
    "generation_batch": {
        "batch_id": manifest.get("batch_id"),
        "method": "single-reference image-to-video (data-uri), parallel submit + independent poll, failure-isolated",
        "scene_results": [
            {"scene_id": t["scene_id"], "task_id": t.get("task_id"), "status": t.get("status"),
             "model": t.get("model"), "error": t.get("error")} for t in manifest.get("tasks", [])
        ],
    },
    "agnes_api_findings": {
        "v2.0_text_to_video": "HTTP 200 -> completed -> downloadable (REAL clip salvaged)",
        "v2.0_image_to_video": "HTTP 429 rate_limit_exceeded (free-tier video quota) ; large data-uri body also 400 invalid_json",
        "v2.5_flash": "HTTP 429 rate_limit_exceeded (free-tier video quota)",
        "model_catalog": "GET /v1/models -> 200 (agnes-video-2.5-flash, agnes-video-v2.0, agnes-video-2.5 present)",
        "blocker": "Free-tier Agnes video-generation quota exhausted (429) + gateway rejects oversized in-body data-URIs (400). Not bypassable without upgrading plan / changing key / changing gateway / changing timeout - all forbidden by task rules.",
    },
    "salvaged_real_clips": [
        {"file": s, "source": "agnes-video-v2.0 text-to-video (HTTP 200)", "ffprobe": ffprobe(s)} for s in salvaged
    ],
    "downstream_demo": {
        "clip_files": [os.path.basename(s) for s in salvaged],
        "final": {"file": DEMOfinal, "ffprobe": ffprobe(DEMOfinal),
                  "decode_check_rc": (subprocess.run(["/usr/bin/ffmpeg", "-v", "error", "-i", DEMOfinal, "-f", "null", "-"],
                                                     capture_output=True, text=True).returncode if os.path.exists(DEMOfinal) else None)},
    },
    "final_status": {
        "PRODUCTION_VERIFIED": False,
        "reason": "5-scene image-to-video generation is BLOCKED by Agnes free-tier video quota (HTTP 429) and gateway body-size (HTTP 400). Not bypassable within task constraints (no plan upgrade / no key change / no gateway change / no timeout change). Downstream chain (download->ffprobe->704to720->concat->verify) IS proven working on Ubuntu with real salvaged Agnes clips.",
        "verified_capabilities_on_ubuntu": [
            "Ubuntu OpenClaw 2026.9.4 host reached via SSH",
            "Agnes provider + video models registered (real)",
            "Agnes v2.0 text-to-video generation -> completed -> download (REAL)",
            "ffprobe on real clip = 704x1280/h264/yuv420p/24fps",
            "ffmpeg 704->720 normalization + concat -> 720x1280/9:16/h264/yuv420p/24fps",
            "final full-decode check = RC 0 / no errors",
            "parallel submit + independent poll + failure isolation (5 tasks logged, single failure did not abort batch)",
        ],
        "not_yet_verified": [
            "5 real image-to-video scene clips on this account (blocked by free-tier video quota 429 + data-uri body 400)",
            "5-scene final 30s MP4 from 5 scene clips",
        ],
    },
    "security": {"api_key_in_report": False, "api_key_masked_prefix": "sk-dV4...", "key_source": "~/.openclaw/openclaw.json (models.providers.agnes)"},
}
os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
with open(os.path.join(ROOT, "reports", "production-report.json"), "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

md = [
    "# AGNES 5-SCENE VIDEO PIPELINE — PRODUCTION VERIFICATION REPORT (Ubuntu)",
    "",
    f"- Generated: {report['generated_at']}",
    f"- Host: {report['environment']['host']} · {report['environment']['os']}",
    f"- OpenClaw {report['environment']['openclaw']} · Node {report['environment']['node']} · Python {report['environment']['python']} · FFmpeg {report['environment']['ffmpeg']}",
    "",
    "## 1. Environment",
    f"- Agnes provider: registered (baseUrl {report['environment']['agnes_provider'].split('baseUrl ')[-1].rstrip(')')}), apiKey present (masked sk-dV4...)",
    f"- Video models: {report['environment']['agnes_video_models']}",
    f"- mediaModel.video.primary: {report['environment']['mediaModel_video_primary']}",
    "",
    "## 2. Input",
    "- 5 reference images (scene01..05.jpg) + 5 scene prompts (scenes.json)",
    "",
    "## 3. Scene Results (generation_batch)",
    "| Scene | Task | Status | Error |",
    "|---|---|---|---|",
]
for s in report["generation_batch"]["scene_results"]:
    md.append(f"| {s['scene_id']} | {str(s['task_id'])[:16] or '-'}… | {s['status']} | {s['error']} |")
md += [
    "",
    "## 4. Agnes API Findings (honest, real calls)",
    "- v2.0 text-to-video: HTTP 200 -> completed -> downloadable (**REAL clip salvaged**)",
    "- v2.0 image-to-video: HTTP 429 rate_limit_exceeded (free-tier video quota); oversized data-uri body -> 400 invalid_json",
    "- v2.5-flash: HTTP 429 rate_limit_exceeded (free-tier video quota)",
    "- **Blocker:** free-tier Agnes video-generation quota exhausted (429) + gateway body-size limit (400). Cannot be bypassed within task constraints (no plan upgrade / no key change / no gateway change / no timeout change).",
    "",
    "## 5. Salvaged Real Clips (proven Ubuntu->Agnes chain)",
]
for c in report["salvaged_real_clips"]:
    p = c["ffprobe"]
    md.append(f"- `{os.path.basename(c['file'])}` ({c['source']}): {p['w']}x{p['h']} {p['codec']}/{p['pix']} {p['fps']} {p['dur']}s audio={p['audio']}")
dm = report["downstream_demo"]
p = dm["final"]["ffprobe"]
md += [
    "",
    "## 6. Downstream Chain Proof (normalize + concat + verify)",
    f"- ffmpeg 704->720 re-encode + concat -> `{os.path.basename(DEMOfinal)}`: {p['w']}x{p['h']} {p['codec']}/{p['pix']} {p['fps']} {p['dur']}s",
    f"- full decode check: RC {dm['final']['decode_check_rc']} (0 = clean)",
    "",
    "## 7. Final Status",
    f"- **PRODUCTION VERIFIED: {report['final_status']['PRODUCTION_VERIFIED']}**",
    f"- Reason: {report['final_status']['reason']}",
    "### Verified on Ubuntu",
]
md += [f"- {x}" for x in report["final_status"]["verified_capabilities_on_ubuntu"]]
md += ["### Not yet verified", ""]
md += [f"- {x}" for x in report["final_status"]["not_yet_verified"]]
md += [
    "",
    "## 8. Security",
    "- API key NOT written to this report or any log/manifest; shown only as masked prefix sk-dV4... .",
]
with open(os.path.join(ROOT, "reports", "production-report.md"), "w") as f:
    f.write("\n".join(md))
print("REPORT WRITTEN")
print(json.dumps({"PRODUCTION_VERIFIED": report["final_status"]["PRODUCTION_VERIFIED"],
                  "salvaged_clips": len(salvaged), "final_demo": dm["final"]["ffprobe"]}, indent=2))
