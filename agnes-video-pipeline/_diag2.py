import json, os, re, time, urllib.request, urllib.error, base64

def load_key():
    return json.load(open(os.path.expanduser("~/.openclaw/openclaw.json")))["models"]["providers"]["agnes"]["apiKey"]

key = load_key()
base = "https://apihub.agnes-ai.cn/v1"

def scrub(s):
    return re.sub(r"sk-[A-Za-z0-9]{6,}", "sk-REDACTED", s)

def call(method, url, payload=None, timeout=120):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data,
        headers={"Authorization": f"Bearer {key}", "Content-Type":"application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")
    except Exception as e:
        return "ERR", str(e)

# 1) model catalog
code, body = call("GET", base+"/models")
print(f"### GET /models -> {code}")
print(scrub(body)[:1500])
print()

img = base64.b64encode(open("/home/ubuntu/.openclaw/workspace/agnes-video-pipeline/input/scene01.jpg","rb").read()).decode()
du = "data:image/jpeg;base64," + img

tests = {
  "v2.0 curl-doc (no img, w/h/frames/fps)": {"model":"agnes-video-v2.0","prompt":"A man turns","width":720,"height":1280,"num_frames":145,"frame_rate":24},
  "v2.0 with base64-string image field": {"model":"agnes-video-v2.0","prompt":"A man turns","seconds":6,"images":du},
  "2.5 text-to-video tiny": {"model":"agnes-video-2.5-flash","prompt":"A man turns","seconds":4},
}
for name, payload in tests.items():
    time.sleep(3)
    code, body = call("POST", base+"/videos", payload)
    print(f"===== {name} -> HTTP {code}")
    print(scrub(body)[:600])
    print()
