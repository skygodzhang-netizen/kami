import json, os, time, base64, urllib.request, urllib.error

def load_key():
    return json.load(open(os.path.expanduser("~/.openclaw/openclaw.json")))["models"]["providers"]["agnes"]["apiKey"]

key = load_key()
base = "https://apihub.agnes-ai.cn/v1"
task = "task_N888nLB5R5GYut9axTkqrO6OHnVjOUSp"  # v2.0 text-to-video accepted earlier (HTTP 200)

def status():
    req = urllib.request.Request(base+"/videos/"+task, headers={"Authorization": f"Bearer {key}","Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, r.read().decode("utf-8","replace")

out = "/home/ubuntu/.openclaw/workspace/agnes-video-pipeline/runtime/salvage/N888.mp4"
os.makedirs(os.path.dirname(out), exist_ok=True)
j = None
for i in range(36):  # up to ~3 min
    try:
        code, body = status()
        j = json.loads(body)
        st = str(j.get("status","")).lower()
        url = j.get("video_url") or j.get("url") or (j.get("data") or {}).get("video_url")
        print(f"[{i}] status={st} http={code} url={'Y' if url else 'N'}", flush=True)
        if st in ("completed","success") or url:
            if url:
                data = urllib.request.urlopen(url, timeout=300).read()
                open(out,"wb").write(data)
                print("DOWNLOADED", out, len(data), "bytes")
            break
        if st in ("failed","error","cancelled"):
            print("FAILED:", j.get("error") or j.get("message"))
            break
        time.sleep(5)
    except urllib.error.HTTPError as e:
        print("poll http", e.code, e.read().decode("utf-8","replace")[:300]); time.sleep(5)
    except Exception as e:
        print("poll err", e); time.sleep(5)

# ffprobe
import subprocess
p = subprocess.run(["ffprobe","-v","error","-print_format","json","-show_format","-show_streams",out], capture_output=True, text=True)
try:
    d = json.loads(p.stdout)
    v = next((s for s in d.get("streams",[]) if s.get("codec_type")=="video"), {})
    f = d.get("format",{})
    print("FFPROBE:", json.dumps({"dur":f.get("duration"),"w":v.get("width"),"h":v.get("height"),"codec":v.get("codec_name"),"pix":v.get("pix_fmt"),"fps":v.get("avg_frame_rate"),"size":f.get("size")}))
except Exception as e:
    print("ffprobe/decode err (file may still be generating):", e, p.stderr[:200])
