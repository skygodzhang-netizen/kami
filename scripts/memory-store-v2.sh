#!/bin/bash
# memory-store-v2.sh — 智能记忆存储
# 带元数据的记忆存储，支持去重和冲突检测

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
TIMESTAMP=$(date "+%Y%m%d-%H%M%S")
CST_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")

# 参数
TYPE="${1:-episode}"
CONTENT="${2:-}"
SOURCE="${3:-manual}"
CONFIDENCE="${4:-high}"
TAGS="${5:-}"

# 验证
if [ -z "$CONTENT" ]; then
    echo "用法: $0 <type> <content> [source] [confidence] [tags]"
    echo ""
    echo "类型: semantic, episode, procedural, preference, environment"
    echo "置信度: high, medium, low"
    echo "来源: manual, automated, system"
    exit 1
fi

# 验证类型
case "$TYPE" in
    semantic|episode|procedural|preference|environment) ;;
    *) echo "未知类型: $TYPE"; exit 1 ;;
esac

# 验证置信度
case "$CONFIDENCE" in
    high|medium|low) ;;
    *) echo "未知置信度: $CONFIDENCE"; exit 1 ;;
esac

# 目标目录
TARGET_DIR="$MEM_BASE/$TYPE"
mkdir -p "$TARGET_DIR"

# 生成 ID
MEMORY_ID="${TYPE}-${TIMESTAMP}"
FILENAME="${MEMORY_ID}.md"
FILEPATH="$TARGET_DIR/$FILENAME"

# 去重检测
if [ -f "$FILEPATH" ]; then
    echo "⚠️  文件已存在: $FILEPATH"
    echo "  将追加内容而非覆盖"
    echo "" >> "$FILEPATH"
    echo "---" >> "$FILEPATH"
else
    # 创建新文件
    cat > "$FILEPATH" << EOF
# 记忆: $MEMORY_ID

## 元数据
- **类型**: $TYPE
- **来源**: $SOURCE
- **置信度**: $CONFIDENCE
- **创建时间**: $CST_TIMESTAMP
- **最后更新**: $CST_TIMESTAMP
- **标签**: $TAGS
- **状态**: active

## 内容
$CONTENT

---
*由 memory-store-v2.sh 自动生成*
EOF
fi

echo "✅ 记忆已存储"
echo "  ID: $MEMORY_ID"
echo "  路径: $FILEPATH"
echo "  类型: $TYPE"
echo "  置信度: $CONFIDENCE"
echo "  来源: $SOURCE"
echo ""

# 运行 Judge 评估
bash "$HOME/.openclaw/workspace/scripts/memory-judge-v2.sh" "$CONTENT" "$TYPE" "$SOURCE"

# 更新索引
bash "$HOME/.openclaw/workspace/scripts/memory-index.sh" > /dev/null 2>&1 || true
