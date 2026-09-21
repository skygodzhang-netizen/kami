import json, os, re, time, urllib.request, urllib.error, base64, subprocess

def load_key():
    return json.load(open(os.path.expanduser("~/.openclaw/openclaw.json")))["models"]["providers"]["agnes"]["apiKey"]

key = load_key(); base = "https://apihub.agnes-ai.cn/v1"
def scrub(s): return re.sub(r"sk-[A-Za-z0-9]{6,}", "sk-REDACTED", s)
def post(payload):
    req = urllib.request.Request(base+"/videos", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r: return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8","replace")
    except Exception as e: return "ERR", str(e)

img_small = base64.b64encode(open("/home/ubuntu/.openclaw/workspace/agnes-video-pipeline/input/scene01.jpg","rb").read()).decode()
# downscale to reduce body: use ffmpeg to make a small jpeg
import tempfile
try:
    subprocess.run(["ffmpeg","-y","-i","/home/ubuntu/.openclaw/workspace/agnes-video-pipeline/input/scene01.jpg",
        "-vf","scale=160:272","-q:v","8",tempfile.gettempdir()+"/s160.jpg"],capture_output=True)
    img_small = base64.b64encode(open(tempfile.gettempdir()+"/s160.jpg","rb").read()).decode()
except Exception as e:
    print("downscale err", e)

tests = {
  "A_txt_v2.0_min":      {"model":"agnes-video-v2.0","prompt":"A man turns","width":704,"height":1280,"num_frames":145,"frame_rate":24},
  "B_img_v2.0_small":    {"model":"agnes-video-v2.0","prompt":"A man turns","width":704,"height":1280,"num_frames":145,"frame_rate":24,"images":[{"url":"data:image/jpeg;base64,"+img_small}]},
  "C_txt_2.5_min":       {"model":"agnes-video-2.5-flash","prompt":"A man turns","width":704,"height":1280,"num_frames":145,"frame_rate":24},
}
for name,pay in tests.items():
    code,body = post(pay)
    m = ""
    if code==200:
        try:
            j=json.loads(body); m=f" id={j.get('id') or j.get('task_id')} status={j.get('status')} size={j.get('size')}"
        except: pass
    print(f"{name} -> HTTP {code}{m} :: {scrub(body)[:220]}")
    time.sleep(4)
