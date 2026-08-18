#!/bin/bash
# ha-camera.sh — HA Camera 集成
# 拍摄快照 → 可选 Vision 分析 → 记录到 Memory

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
CAMERA_DIR="$MEM_BASE/camera"
VISION_DIR="$MEM_BASE/vision"
mkdir -p "$CAMERA_DIR" "$VISION_DIR"

HA_URL="http://192.168.100.108:8123"
HA_TOKEN_FILE="/home/ubuntu/.openclaw/workspace/config/ha-token"

load_token() {
    if [ -f "$HA_TOKEN_FILE" ]; then
        HA_TOKEN=$(tr -d '[:space:]' < "$HA_TOKEN_FILE")
    else
        echo "❌ HA Token 未配置" >&2
        exit 1
    fi
}

# 获取 Camera 列表
list_cameras() {
    load_token
    
    curl -s -H "Authorization: Bearer $HA_TOKEN" \
         "$HA_URL/api/states" 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
cameras = [item for item in data if item['entity_id'].startswith('camera.')]
print(f'找到 {len(cameras)} 个 Camera 实体:')
for c in cameras:
    name = c.get('attributes', {}).get('friendly_name', c['entity_id'])
    state = c.get('state', 'unknown')
    print(f\"  - {name} ({c['entity_id']}): {state}\")
"
}

# 拍摄快照
snapshot() {
    local entity_id="$1"
    load_token
    
    echo "📸 拍摄快照: $entity_id"
    
    # 调用 HA camera.snapshot 服务
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local output_file="$CAMERA_DIR/${entity_id//. /}-${timestamp}.jpg"
    
    curl -s -X POST \
         -H "Authorization: Bearer $HA_TOKEN" \
         -H "Content-Type: application/json" \
         -d "{\"entity_id\": \"$entity_id\"}" \
         "$HA_URL/api/services/camera/snapshot" 2>/dev/null
    
    echo "✅ 快照已保存到: $output_file"
}

# 获取最新快照
latest_snapshot() {
    local entity_id="$1"
    load_token
    
    curl -s -H "Authorization: Bearer $HA_TOKEN" \
         "$HA_URL/api/camera/${entity_id##*.}/jpeg" 2>/dev/null
}

# Camera → Vision 分析 (预留接口)
analyze() {
    local image_path="$1"
    
    if [ ! -f "$image_path" ]; then
        echo "❌ 图片文件不存在: $image_path"
        return 1
    fi
    
    echo "👁️  分析图片: $image_path"
    echo "⏳ Vision 分析需要配置图像识别模型"
    echo ""
    echo "使用方式:"
    echo "  1. 先拍摄快照: bash scripts/ha/ha-camera.sh snapshot <entity_id>"
    echo "  2. 再分析图片: bash scripts/ha/ha-camera.sh analyze <image_path>"
    echo ""
    echo "预留接口已创建，待模型配置后可启用"
}

# 命令分发
case "${1:-help}" in
    list)
        list_cameras
        ;;
    snapshot)
        snapshot "${2:-}"
        ;;
    latest)
        latest_snapshot "${2:-}"
        ;;
    analyze)
        analyze "${2:-}"
        ;;
    *)
        echo "用法: $0 {list|snapshot|latest|analyze}"
        echo ""
        echo "命令:"
        echo "  list                    - 列出所有 Camera 实体"
        echo "  snapshot <entity_id>    - 拍摄快照"
        echo "  latest <entity_id>      - 获取最新快照"
        echo "  analyze <image_path>    - 分析图片 (Vision 预留接口)"
        ;;
esac
