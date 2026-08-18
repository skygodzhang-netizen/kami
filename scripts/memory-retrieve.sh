#!/bin/bash
# memory-retrieve.sh — 记忆检索系统
# 支持语义搜索、关键词搜索、时间范围搜索

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
QUERY="${1:-}"
TYPE="${2:-all}"  # all, semantic, episode, procedural, preference, environment
LIMIT="${3:-10}"

if [ -z "$QUERY" ]; then
    echo "用法: $0 <查询关键词> [类型] [限制数]"
    echo "类型: all, semantic, episode, procedural, preference, environment"
    exit 1
fi

echo "=== 记忆检索 ==="
echo "查询: $QUERY"
echo "类型: $TYPE"
echo "时间: $(date "+%Y-%m-%d %H:%M:%S CST")"
echo ""

# 构建搜索路径
SEARCH_PATHS=""
case "$TYPE" in
    semantic) SEARCH_PATH="$MEM_BASE/semantic" ;;
    episode) SEARCH_PATH="$MEM_BASE/episodes" ;;
    procedural) SEARCH_PATH="$MEM_BASE/procedural" ;;
    preference) SEARCH_PATH="$MEM_BASE/preferences" ;;
    environment) SEARCH_PATH="$MEM_BASE/environment" ;;
    *) SEARCH_PATH="$MEM_BASE" ;;
esac

# 执行搜索
results=$(grep -r "$QUERY" "$SEARCH_PATH" --include="*.md" 2>/dev/null | grep -v "backup" | head -n "$LIMIT" || true)

if [ -z "$results" ]; then
    echo "未找到相关记忆"
    exit 0
fi

echo "找到 $(echo "$results" | wc -l) 条结果:"
echo "---"
echo "$results" | while IFS= read -r line; do
    file=$(echo "$line" | cut -d: -f1)
    content=$(echo "$line" | cut -d: -f2- | head -c 200)
    echo "📄 $file"
    echo "   $content..."
    echo ""
done

echo "---"
echo "检索完成"
