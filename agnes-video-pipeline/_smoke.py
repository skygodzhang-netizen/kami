import sys
sys.path.insert(0, "/home/ubuntu/.openclaw/workspace/agnes-video-pipeline")
import json, os
from pipeline import load_key, submit_scene, PIPELINE_ROOT, log

load_key()
cfg = json.load(open(os.path.join(PIPELINE_ROOT, "scenes.json")))
s = cfg["scenes"][0]
# minimal temp batch for smoke
batch = os.path.join(PIPELINE_ROOT, "runtime", "smoke")
os.makedirs(os.path.join(batch, "requests"), exist_ok=True)
os.makedirs(os.path.join(batch, "logs"), exist_ok=True)
rec = submit_scene(s, cfg["global"]["model_primary"], batch)
print(json.dumps({k: rec.get(k) for k in ("scene_id","model","task_id","status","submit_http","error","submit_time_seconds")}, indent=2))
log("SMOKE submit done task_id=" + str(rec.get("task_id")), os.path.join(batch, "logs", "smoke.log"))
