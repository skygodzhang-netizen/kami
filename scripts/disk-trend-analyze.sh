#!/bin/bash
# disk-trend-analyze.sh — 磁盘用量趋势采集
# 采集各分区用量数据，追加到趋势文件
# 合并到晚检使用，也可独立调用

set -euo pipefail

TREND_FILE="/home/ubuntu/.openclaw/workspace/config/disk-trend.json"
TIMESTAMP_CST=$(date "+%Y-%m-%d %H:%M:%S CST")

echo "[$TIMESTAMP_CST] 开始采集磁盘趋势数据..."
echo ""

python3 << 'PYEOF'
import json, datetime, subprocess

trend_file = "/home/ubuntu/.openclaw/workspace/config/disk-trend.json"
ts_cst = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S CST")

entry = {
    "timestamp": ts_cst,
    "ubuntu": {},
    "istoreos": {}
}

# Ubuntu disk
try:
    out = subprocess.check_output(["df", "-h", "/", "/home"], text=True, timeout=5)
    for line in out.strip().split("\n")[1:]:
        parts = line.split()
        if len(parts) >= 6:
            mount = parts[5]
            entry["ubuntu"][f"disk_{mount}"] = {"size": parts[1], "used": parts[2], "avail": parts[3], "pct": parts[4]}
except: pass

# Ubuntu system
try:
    out = subprocess.check_output(["uptime"], text=True, timeout=5)
    entry["ubuntu"]["uptime"] = out.strip()
except: pass

try:
    out = subprocess.check_output(["free", "-h"], text=True, timeout=5)
    for line in out.split("\n"):
        if line.startswith("Mem:"):
            parts = line.split()
            entry["ubuntu"]["mem_total"] = parts[1]
            entry["ubuntu"]["mem_used"] = parts[2]
            entry["ubuntu"]["mem_avail"] = parts[6]
            break
except: pass

# iStoreOS disk
try:
    out = subprocess.check_output(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
         "root@192.168.100.1",
         "df -h /overlay /mnt/sata2-4 /mnt/data_sda1 2>/dev/null | awk 'NR>1 {print $6, $5}'"],
        text=True, timeout=10
    )
    for line in out.strip().split("\n"):
        parts = line.split()
        if len(parts) >= 2:
            mount = parts[0].replace("/mnt/", "").replace("/", "_")
            entry["istoreos"][f"disk_{mount}"] = {"pct": parts[1]}
except: pass

try:
    out = subprocess.check_output(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
         "root@192.168.100.1", "uptime"], text=True, timeout=5)
    entry["istoreos"]["uptime"] = out.strip()
except: pass

try:
    out = subprocess.check_output(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
         "root@192.168.100.1", "free -m"], text=True, timeout=5)
    for line in out.split("\n"):
        if line.startswith("Mem:"):
            parts = line.split()
            total = int(parts[1])
            used = int(parts[2])
            pct = round(used * 100 / total) if total > 0 else 0
            entry["istoreos"]["mem_pct"] = f"{pct}%"
            break
except: pass

# Load existing data and append
try:
    with open(trend_file, "r") as f:
        raw = json.load(f)
    if isinstance(raw, list):
        entries = raw
    elif isinstance(raw, dict) and "entries" in raw:
        entries = raw["entries"]
    else:
        entries = []
except:
    entries = []

entries.append(entry)

if len(entries) > 2160:
    entries = entries[-2160:]

with open(trend_file, "w") as f:
    json.dump({"entries": entries}, f, indent=2, ensure_ascii=False)

print(f"趋势数据已更新: {ts_cst}")
PYEOF
