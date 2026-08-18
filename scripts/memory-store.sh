#!/bin/bash
# memory-store.sh — 记忆存储系统
# 支持带元数据的故事记忆存储

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
TYPE="${1:-episode}"  # semantic, episode, procedural, preference, environment
CONTENT="${2:-}"
SOURCE="${3:-manual}"
CONFIDENCE="${4:-high}"  # high, medium, low
TAGS="${5:-}"

# 生成 ID
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
MEMORY_ID="${TYPE}-${TIMESTAMP}"

# 验证输入
if [ -z "$CONTENT" ]; then
    echo "用法: $0 <type> <content> [source] [confidence] [tags]"
    echo "类型: semantic, episode, procedural, preference, environment"
    echo "置信度: high, medium, low"
    exit 1
fi

# 目标目录
case "$TYPE" in
    semantic) TARGET_DIR="$MEM_BASE/semantic" ;;
    episode) TARGET_DIR="$MEM_BASE/episodes" ;;
    procedural) TARGET_DIR="$MEM_BASE/procedural" ;;
    preference) TARGET_DIR="$MEM_BASE/preferences" ;;
    environment) TARGET_DIR="$MEM_BASE/environment" ;;
    *) echo "未知类型: $TYPE"; exit 1 ;;
esac

mkdir -p "$TARGET_DIR"

# 生成记忆文件
FILENAME="$TARGET_DIR/${MEMORY_ID}.md"

cat > "$FILENAME" << EOF
# 记忆: $MEMORY_ID

## 元数据
- **类型**: $TYPE
- **来源**: $SOURCE
- **置信度**: $CONFIDENCE
- **创建时间**: $(date "+%Y-%m-%d %H:%M:%S CST")
- **最后更新**: $(date "+%Y-%m-%d %H:%M:%S CST")
- **标签**: $TAGS

## 内容
$CONTENT

---
*由 memory-store.sh 自动生成*
EOF

echo "✅ 记忆已存储"
echo "  ID: $MEMORY_ID"
echo "  路径: $FILENAME"
echo "  类型: $TYPE"
echo "  置信度: $CONFIDENCE"
echo ""

# 运行质量评估
bash "$MEM_BASE/../scripts/memory-judge.sh" "$TYPE" "$CONTENT" "$MEMORY_ID"
