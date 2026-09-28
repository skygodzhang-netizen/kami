#!/usr/bin/env python3
"""Five-scene Agnes Video 2.5 Flash orchestration using durable worker state."""
import json, os, shutil, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path("/home/ubuntu/.openclaw/workspace/agnes-video-pipeline")
sys.path.insert(0,str(ROOT))
from agnes_video_worker import submit, poll, MODEL
from pipeline_concat import concat, verify

def write_manifest(path, batch_id, states):
    value={"schema":2,"batch_id":batch_id,"model":MODEL,"updated_at":datetime.now(timezone.utc).isoformat(),
           "tasks":[{"scene_id":s.get("scene_id") or s.get("scene"),"primary_model":s.get("primary_model"),
                     "primary_attempts":s.get("primary_attempts"),"primary_task_id":s.get("primary_task_id"),
                     "fallback_triggered":s.get("fallback_triggered"),"fallback_reason":s.get("fallback_reason"),
                     "fallback_model":s.get("fallback_model"),"fallback_attempts":s.get("fallback_attempts"),
                     "fallback_task_id":s.get("fallback_task_id"),"active_model":s.get("active_model"),
                     "status":s.get("status"),"error":s.get("last_error")} for s in states]}
    tmp=path.with_suffix(".tmp"); tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)); os.replace(tmp,path)

def main():
    batch_id="video-batches-"+datetime.now().strftime("%Y%m%d-%H%M%S")
    batch=ROOT/"runtime"/batch_id
    for d in ("requests","tasks","videos","logs","reports","final"): (batch/d).mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/"scenes.json").read_text())
    states=[]; manifest=batch/"manifest.json"
    # Submit sequentially. Every accepted ID is atomically durable before moving on.
    for scene in cfg["scenes"]:
        prompt=(cfg.get("person_lock","")+" "+scene["prompt"]+" "+cfg.get("common_negative","")).strip()
        state_path=batch/"tasks"/(scene["scene_id"]+".json")
        state=submit(state_path,prompt,str(ROOT/scene["image"]),scene["scene_id"])
        states.append(state); write_manifest(manifest,batch_id,states)
        if state.get("primary_task_id") or state.get("fallback_task_id") or state.get("video_id"): time.sleep(8)
    # Poll only accepted IDs. Two workers avoid provider bursts; resume never POSTs.
    def resume(scene):
        return poll(batch/"tasks"/(scene["scene_id"]+".json"),batch/"videos"/(scene["scene_id"]+".mp4"))
    accepted=[s for s in cfg["scenes"] if any(json.loads((batch/"tasks"/(s["scene_id"]+".json")).read_text()).get(k) for k in ("primary_task_id","fallback_task_id","video_id"))]
    if accepted:
        with ThreadPoolExecutor(max_workers=2) as ex:
            futures={ex.submit(resume,s):s for s in accepted}
            for f in as_completed(futures):
                st=f.result(); states=[st if x.get("scene")==st.get("scene") else x for x in states]; write_manifest(manifest,batch_id,states)
    records=[]
    for scene in cfg["scenes"]:
        sp=batch/"tasks"/(scene["scene_id"]+".json"); st=json.loads(sp.read_text())
        val=st.get("validation") or {}
        records.append({"scene_id":scene["scene_id"],"task_id":st.get("primary_task_id") or st.get("fallback_task_id") or st.get("video_id"),
                        "primary_result":"PASS" if st.get("primary_task_id") else ("QUEUE_FULL -> FALLBACK" if st.get("fallback_triggered") else "FAIL"),
                        "active_model":st.get("active_model"),"fallback_used":bool(st.get("fallback_triggered")),
                        "status":st.get("status"),"error":st.get("last_error"),
                        "local_file":st.get("output"),"file_size":st.get("bytes"),"ffprobe":{"duration":float(val.get("duration") or 0),"width":val.get("width"),"height":val.get("height"),"codec":val.get("codec"),"pix_fmt":val.get("pix_fmt"),"fps":24},"decode":{"exit":val.get("decode_exit")}})
    completed=[r for r in records if r["status"]=="completed" and r.get("local_file")]
    result={"batch":str(batch),"model":MODEL,"completed":len(completed),"total":5,"status":"generation_incomplete"}
    if len(completed)==5:
        cres=concat(records,cfg["scenes"],str(batch),target_w=720,target_h=1280,fps=24)
        final=batch/"final"/"black_clothing_5scene_final.mp4"; vres=verify(str(final),5)
        result.update({"status":"completed" if vres.get("pass") else "validation_error","concat":cres,"validation":vres,"final":str(final)})
        if vres.get("pass"):
            (ROOT/"final").mkdir(exist_ok=True); shutil.copyfile(final,ROOT/"final"/final.name)
    (batch/"reports"/"production-report.json").write_text(json.dumps({"generated_at":datetime.now(timezone.utc).isoformat(),"result":result,"scenes":records},ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result["status"]=="completed" else 2
if __name__=="__main__": raise SystemExit(main())
