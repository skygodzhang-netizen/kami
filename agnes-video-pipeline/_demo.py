import json, os, time, base64, urllib.request, urllib.error, subprocess, shutil

def load_key():
    return json.load(open(os.path.expanduser("~/.openclaw/openclaw.json")))["models"]["providers"]["agnes"]["apiKey"]

key = load_key(); base = "https://apihub.agnes-ai.cn/v1"
FF="/usr/bin/ffmpeg"; FFP="/usr/bin/ffprobe"
ROOT="/home/ubuntu/.openclaw/workspace/agnes-video-pipeline"
demo=os.path.join(ROOT,"runtime","downstream_demo"); os.makedirs(demo,exist_ok=True)

def status(t):
    r=urllib.request.Request(base+"/videos/"+t,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: return x.read().decode("utf-8","replace")

# Salvage the freshly queued v2.0 text clip + the earlier N888
tasks = [
 ("task_QMTieDyJAnDQ5IyNtE5twoeezqi8JC9l","v20_txt_QMTieDyJ.mp4"),
 ("task_N888nLB5R5GYut9axTkqrO6OHnVjOUSp","v20_txt_N888.mp4"),
]
clips=[]
for t,name in tasks:
    out=os.path.join(demo,name)
    if os.path.exists(out) and os.path.getsize(out)>0:
        clips.append(out); print(f"reuse {name}"); continue
    for i in range(40):
        body=status(t); j=json.loads(body); st=str(j.get("status","")).lower()
        url=j.get("video_url") or j.get("url") or (j.get("data") or {}).get("video_url")
        if st in("completed","success") or url:
            if url:
                open(out,"wb").write(urllib.request.urlopen(url,timeout=300).read())
                clips.append(out); print(f"salvaged {name} ({os.path.getsize(out)} bytes)"); break
        if st in("failed","error","cancelled"):
            print(f"{name} FAILED {j.get('error') or j.get('message')}"); break
        time.sleep(5)

def ffprobe(p):
    d=json.loads(subprocess.check_output([FFP,"-v","error","-print_format","json","-show_format","-show_streams",p],text=True))
    v=next((s for s in d["streams"] if s["codec_type"]=="video"),{})
    a=next((s for s in d["streams"] if s["codec_type"]=="audio"),None)
    return {"dur":float(d["format"]["duration"]),"w":v.get("width"),"h":v.get("height"),"codec":v.get("codec_name"),
            "pix":v.get("pix_fmt"),"fps":v.get("avg_frame_rate"),"size":d["format"].get("size"),
            "audio":(a.get("codec_name") if a else None),"ar":(a.get("sample_rate") if a else None)}

print("\n=== salvaged clip ffprobe ===")
for c in clips: print(os.path.basename(c), ffprobe(c))

# Prove 704->720 normalization + concat on the real salvaged clips (downstream chain demo)
if len(clips)>=1:
    files=clips
    inp=[]
    for p in files: inp+=["-i",p]
    n=len(files)
    parts=[f"[{i}:v]scale=720:1280:flags=lanczos,setsar=1,fps=24[v{i}]" for i in range(n)]
    parts.append("".join(f"[v{i}]" for i in range(n))+f"concat=n={n}:v=1:a=0[vout]")
    fc=";".join(parts)
    out=os.path.join(demo,"downstream_demo_final.mp4")
    cmd=[FF,"-y"]+inp+["-filter_complex",fc,"-map","[vout]","-c:v","libx264","-profile:v","high",
         "-level","4.0","-pix_fmt","yuv420p","-r","24","-movflags","+faststart",out]
    proc=subprocess.run(cmd,capture_output=True,text=True)
    print("\n=== ffmpeg normalize+concat RC", proc.returncode, (proc.stderr or"")[-400:])
    if proc.returncode==0 and os.path.exists(out):
        print("=== final ffprobe ===", ffprobe(out))
        dc=subprocess.run([FF,"-v","error","-i",out,"-f","null","-"],capture_output=True,text=True)
        print("=== full decode check RC", dc.returncode, "errors:", (dc.stderr.strip() or "none"))
