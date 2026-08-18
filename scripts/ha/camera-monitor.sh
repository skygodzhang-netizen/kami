#!/bin/bash
# camera-monitor.sh — Camera 监控脚本
# 定期检查摄像头在线状态，离线时通知

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
CAMERA_DIR="$MEM_BASE/camera"
NOTIFICATION_QUEUE="$MEM_BASE/ha-notifications/queue.txt"
LOG_FILE="$MEM_BASE/camera-monitor.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")

echo "[$TIMESTAMP] === Camera 监控开始 ===" >> "$LOG_FILE"

# 获取所有摄像头配置
ONLINE_COUNT=0
TOTAL_COUNT=0

for cam_file in "$CAMERA_DIR"/*.json; do
    [ -f "$cam_file" ] || continue
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    
    CAM_NAME=$(python3 -c "import json; print(json.load(open('$cam_file'))['name'])" 2>/dev/null)
    CAM_IP=$(python3 -c "import json; print(json.load(open('$cam_file'))['ip'])" 2>/dev/null)
    
    [ -z "$CAM_NAME" ] || [ -z "$CAM_IP" ] && continue
    
    echo "[$TIMESTAMP] 检查: $CAM_NAME ($CAM_IP)" >> "$LOG_FILE"
    
    # 检测在线状态
    if ping -c 1 -W 2 "$CAM_IP" >/dev/null 2>&1; then
        echo "[$TIMESTAMP] ✅ $CAM_NAME 在线" >> "$LOG_FILE"
        ONLINE_COUNT=$((ONLINE_COUNT + 1))
        
        # 更新配置
        python3 -c "
import json
with open('$cam_file') as f:
    d = json.load(f)
d['status'] = 'online'
d['last_seen'] = '$TIMESTAMP'
with open('$cam_file', 'w') as f:
    json.dump(d, f, indent=2)
" 2>/dev/null
    else
        echo "[$TIMESTAMP] ❌ $CAM_NAME 离线" >> "$LOG_FILE"
        
        # 更新配置
        python3 -c "
import json
with open('$cam_file') as f:
    d = json.load(f)
d['status'] = 'offline'
with open('$cam_file', 'w') as f:
    json.dump(d, f, indent=2)
" 2>/dev/null
        
        # 写入通知队列
        echo "[$TIMESTAMP] $CAM_NAME 离线" >> "$NOTIFICATION_QUEUE"
    fi
done

echo "[$TIMESTAMP] === Camera 监控完成 ===" >> "$LOG_FILE"

# 输出摘要
echo "Camera: $ONLINE_COUNT/$TOTAL_COUNT 在线"
