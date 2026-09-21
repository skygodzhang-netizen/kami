import os, json

WS = os.path.expanduser("~/.openclaw/workspace")
PIPE = os.path.join(WS, "agnes-video-pipeline")
SKILL = os.path.join(WS, "skills", "agnes-video-pipeline")

print("=== SKILL tree ===")
for r, d, fs in os.walk(SKILL):
    for x in sorted(fs):
        p = os.path.join(r, x)
        print(" ", os.path.relpath(p, SKILL), os.path.getsize(p))

print("=== memory file ===")
mp = os.path.join(WS, "memory", "agnes-video-pipeline-workflow.md")
print("  exists:", os.path.exists(mp), "size:", os.path.getsize(mp) if os.path.exists(mp) else 0)

print("=== pipeline artifacts (retained) ===")
for sub in ["input", "reports", "runtime/downstream_demo"]:
    p = os.path.join(PIPE, sub)
    if os.path.isdir(p):
        for x in sorted(os.listdir(p)):
            fp = os.path.join(p, x)
            print(f"  {sub}/{x}  ({os.path.getsize(fp)} b)" if os.path.isfile(fp) else f"  {sub}/{x}/")
    else:
        print("  (missing)", sub)

print("=== latest batch manifest + report ===")
batches = sorted(__import__("glob").glob(os.path.join(PIPE, "runtime", "video-batches-*")))
b = batches[-1] if batches else None
print("  batch:", b)
if b:
    for fn in ["manifest.json", "reports/production-report.json", "reports/production-report.md", "logs/submit.log", "logs/poll.log"]:
        fp = os.path.join(b, fn)
        print(f"  {fn}: exists={os.path.exists(fp)} size={os.path.getsize(fp) if os.path.exists(fp) else 0}")
    m = json.load(open(os.path.join(b, "manifest.json")))
    print("  batch scene statuses:", {t['scene_id']: t['status'] for t in m.get('tasks', [])})

print("=== final report verdict ===")
rp = os.path.join(PIPE, "reports", "production-report.json")
if os.path.exists(rp):
    r = json.load(open(rp))
    print("  PRODUCTION_VERIFIED =", r["final_status"]["PRODUCTION_VERIFIED"])
    print("  key_in_report_leaked =", any("sk-dV4Ek" in json.dumps(v) for v in [r.get("security",{}).get("key_masked")]))
    print("  security block:", r.get("security"))
