#!/usr/bin/env bash
P=/home/ubuntu/.openclaw/workspace/agnes-video-pipeline/runtime
echo "=== last_run.log tail ==="
tail -30 "$P/last_run.log" 2>/dev/null
echo "=== batches ==="
ls -1d "$P"/video-batches-* 2>/dev/null
L=$(ls -1d "$P"/video-batches-* 2>/dev/null | sort | tail -1)
echo "latest_batch=$L"
if [ -n "$L" ] && [ -f "$L/manifest.json" ]; then
  echo "=== manifest ==="
  cat "$L/manifest.json"
  echo "=== videos ==="
  ls -l "$L/videos" 2>/dev/null
  echo "=== final ==="
  ls -l "$L/final" 2>/dev/null
fi
echo "=== run_pipeline proc ==="
ps -ef | grep run_pipeline | grep -v grep || echo "no run_pipeline process"
