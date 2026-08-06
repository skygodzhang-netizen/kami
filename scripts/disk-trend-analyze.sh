#!/bin/bash
# disk-trend-analyze.sh — 磁盘用量趋势采集
# 采集各分区用量数据，追加到趋势文件
# 合并到晚检使用，也可独立调用

set -euo pipefail

TREND_FILE="/home/ubuntu/.openclaw/workspace/config/disk-trend.json"
TIMESTAMP=$(date -u "+%Y-%m-%dT%H:%M:%SZ")
TIMESTAMP_CST=$(date "+%Y-%m-%d %H:%M:%S CST")

# 初始化趋势文件（如果不存在）
if [ ! -f "$TREND_FILE" ]; then
    echo '{"collected":[],"last_update":""}' > "$TREND_FILE"
fi

# 采集 Ubuntu AI Server 磁盘
collect_ubuntu_disk() {
    echo "  [Ubuntu AI Server]"
    df -h / /home 2>/dev/null | awk 'NR>1 {
        printf "    {\"mount\":\"%s\",\"total\":\"%s\",\"used\":\"%s\",\"avail\":\"%s\",\"use_pct\":\"%s\"}\n", $6, $2, $3, $4, $5
    }'
}

# 采集 iStoreOS 磁盘
collect_istoreos_disk() {
    echo "  [iStoreOS Router]"
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.100.1 \
        "df -h /overlay /mnt/sata2-4 /mnt/data_sda1 2>/dev/null | awk 'NR>1 {printf \"    {\\\"mount\\\":\\\"%s\\\",\\\"total\\\":\\\"%s\\\",\\\"used\\\":\\\"%s\\\",\\\"avail\\\":\\\"%s\\\",\\\"use_pct\\\":\\\"%s\\\"}\\n\", \$6, \$2, \$3, \$4, \$5}'" 2>/dev/null || echo "    [SSH 连接失败]"
}

echo "[$TIMESTAMP_CST] 开始采集磁盘趋势数据..."
echo ""

# 采集数据
UBUNTU_DATA=$(collect_ubuntu_disk)
ISTOREOS_DATA=$(collect_istoreos_disk)

echo "$UBUNTU_DATA"
echo ""
echo "$ISTOREOS_DATA"

# 追加到趋势文件（使用 python3 处理 JSON）
python3 << 'PYEOF'
import json
import datetime
import subprocess
import sys

trend_file = "/home/ubuntu/.openclaw/workspace/config/disk-trend.json"

try:
    with open(trend_file, 'r') as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {"collected": [], "last_update": ""}

# 采集当前磁盘数据
def get_df_data(mounts):
    results = []
    try:
        output = subprocess.run(["df", "-h"] + mounts, capture_output=True, text=True, timeout=10)
        lines = output.stdout.strip().split('\n')[1:]  # skip header
        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                results.append({
                    "mount": parts[5],
                    "total": parts[1],
                    "used": parts[2],
                    "avail": parts[3],
                    "use_pct": parts[4]
                })
    except Exception as e:
        results.append({"error": str(e)})
    return results

# 采集 Ubuntu 数据
ubuntu_mounts = ["/", "/home"]
ubuntu_data = get_df_data(ubuntu_mounts)

# 采集 iStoreOS 数据（通过 SSH）
istoreos_mounts = ["/overlay", "/mnt/sata2-4", "/mnt/data_sda1"]
istoreos_data = []
try:
    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
               "root@192.168.100.1",
               "df -h " + " ".join(istoreos_mounts)]
    output = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=15)
    lines = output.stdout.strip().split('\n')[1:]
    for line in lines:
        parts = line.split()
        if len(parts) >= 6:
            istoreos_data.append({
                "host": "istoreos",
                "mount": parts[5],
                "total": parts[1],
                "used": parts[2],
                "avail": parts[3],
                "use_pct": parts[4]
            })
except Exception as e:
    istoreos_data.append({"host": "istoreos", "error": str(e)})

entry = {
    "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "ubuntu": ubuntu_data,
    "istoreos": istoreos_data
}

data["collected"].append(entry)
data["last_update"] = entry["timestamp"]

# 保留最近 90 天的数据（每天1条 × 90 = 90 条）
if len(data["collected"]) > 90:
    data["collected"] = data["collected"][-90:]

with open(trend_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"\n数据已写入 {trend_file}")
print(f"总计采集记录: {len(data['collected'])} 条")
PYEOF

echo ""
echo "[$TIMESTAMP_CST] 磁盘趋势数据采集完成"
