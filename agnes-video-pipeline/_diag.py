import json, os, re, urllib.request, urllib.error

def load_key():
    return json.load(open(os.path.expanduser("~/.openclaw/openclaw.json")))["models"]["providers"]["agnes"]["apiKey"]

key = load_key()
base = "https://apihub.agnes-ai.cn/v1"
img = open("/home/ubuntu/.openclaw/workspace/agnes-video-pipeline/input/scene01.jpg","rb").read()
import base64, mimetypes
du = "data:image/jpeg;base64," + base64.b64encode(img).decode()

def post(payload):
    req = urllib.request.Request(base+"/videos", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8","replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")
    except Exception as e:
        return "ERR", str(e)

def scrub(s):
    return re.sub(r"sk-[A-Za-z0-9]{6,}", "sk-REDACTED", s)

tests = {
  "v2.0_min": {"model":"agnes-video-v2.0","prompt":"A man in a modern bedroom turns 90 degrees","seconds":6,"images":[{"url":du}]},
  "v2.0_noimg": {"model":"agnes-video-v2.0","prompt":"A modern bedroom, a man","seconds":6,"width":720,"height":1280,"num_frames":145,"frame_rate":24},
  "2.5_min": {"model":"agnes-video-2.5-flash","prompt":"A man in a modern bedroom turns 90 degrees","seconds":6,"images":[{"url":du}]},
  "2.5_size": {"model":"agnes-video-2.5-flash","prompt":"A man turns","seconds":6,"size":"720x1280","aspect_ratio":"9:16","images":[{"url":du}]},
}
for name, payload in tests.items():
    code, body = post(payload)
    print(f"===== {name} -> HTTP {code}")
    print(scrub(body)[:800])
    print()
