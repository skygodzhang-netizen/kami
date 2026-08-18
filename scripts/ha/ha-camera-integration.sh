#!/bin/bash
# ha-camera-integration.sh — Camera 集成到 HA
# 将 IP 摄像头添加到 HA 并支持快照/Vision

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
CAMERA_DIR="$MEM_BASE/camera"
VISION_DIR="$MEM_BASE/vision"
HA_CONFIG="/home/ubuntu/homeassistant/config/configuration.yaml"

mkdir -p "$CAMERA_DIR" "$VISION_DIR"

CAMERA_IP="${1:-192.168.100.195}"
CAMERA_NAME="${2:-客厅}"

echo "=== Camera 集成到 HA ==="
echo "IP: $CAMERA_IP"
echo "名称: $CAMERA_NAME"
echo ""

# 1. 检查摄像头可达性
echo "🔍 检查摄像头连通性..."
if ! ping -c 1 -W 1 "$CAMERA_IP" >/dev/null 2>&1; then
    echo "❌ 摄像头不可达: $CAMERA_IP"
    exit 1
fi
echo "✅ 摄像头可达"

# 2. 尝试获取快照
echo ""
echo "📸 尝试获取快照..."
SNAPSHOT_URL=""
for path in "/snapshot.jpg" "/cgi-bin/snapshot.cgi" "/image" "/photo.jpg" "/picture.jpg"; do
    HTTP_CODE=$(curl -s -o /tmp/cam_test.jpg -w "%{http_code}" "http://$CAMERA_IP$path" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] && [ -s /tmp/cam_test.jpg ]; then
        SNAPSHOT_URL="http://$CAMERA_IP$path"
        echo "✅ 快照获取成功: $SNAPSHOT_URL"
        echo "   大小: $(wc -c < /tmp/cam_test.jpg) bytes"
        break
    fi
done

if [ -z "$SNAPSHOT_URL" ]; then
    echo "⚠️  无法自动获取快照 URL，尝试 RTSP 流..."
    RTSP_URL="rtsp://$CAMERA_IP:554/stream1"
    echo "   RTSP URL: $RTSP_URL"
    echo "   请在 HA 中手动配置 RTSP 流"
fi

# 3. 生成 HA 配置
echo ""
echo "📝 生成 HA 配置..."
CAT_CONFIG=$(cat <<EOF

# Camera - $CAMERA_NAME
camera:
  - platform: generic
    name: $CAMERA_NAME
    still_image_url: $SNAPSHOT_URL
    username: !secret camera_username
    password: !secret camera_password
    verify_ssl: false
EOF
)

if [ -n "$SNAPSHOT_URL" ]; then
    echo "✅ 配置生成成功:"
    echo "$CAT_CONFIG"
else
    echo "⚠️  需要手动配置 HA Camera"
    echo ""
    echo "在 HA 中添加以下配置:"
    echo "  配置 → 仪表板 → 侧边栏设置 → 添加集成"
    echo "  搜索 'Generic Camera' 或 'FFmpeg'"
fi

# 4. 保存摄像头信息到 Memory
echo ""
echo "💾 保存摄像头信息到 Memory..."
cat > "$CAMERA_DIR/${CAMERA_NAME}.json" <<EOF
{
  "name": "$CAMERA_NAME",
  "ip": "$CAMERA_IP",
  "snapshot_url": "$SNAPSHOT_URL",
  "rtsp_url": "rtsp://$CAMERA_IP:554/stream1",
  "added_at": "$(date -Iseconds)",
  "status": "pending"
}
EOF
echo "✅ 已保存到: $CAMERA_DIR/${CAMERA_NAME}.json"

# 5. 下一步指引
echo ""
echo "=== 下一步 ==="
echo "1. 在 HA 中添加 Camera 集成:"
echo "   - 配置 → 仪表板 → 侧边栏设置 → 添加集成"
echo "   - 搜索 'Generic Camera'"
echo "   - 输入以上配置"
echo ""
echo "2. 或者使用 FFmpeg 平台 (支持 RTSP):"
echo "   camera:"
echo "     - platform: ffmpeg"
echo "       input: rtsp://$CAMERA_IP:554/stream1"
echo ""
echo "3. 配置完成后，可以使用以下命令:"
echo "   bash scripts/ha/ha-camera.sh list"
echo "   bash scripts/ha/ha-camera.sh snapshot $CAMERA_NAME"
