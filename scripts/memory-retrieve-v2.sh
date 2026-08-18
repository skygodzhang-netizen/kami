#!/bin/bash
# memory-retrieve-v2.sh — 智能记忆检索
# 支持关键词、类型、时间范围、置信度过滤

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
QUERY="${1:-}"
TYPE="${2:-all}"
CONFIDENCE="${3:-all}"
LIMIT="${4:-10}"

if [ -z "$QUERY" ]; then
    echo "用法: $0 <查询> [类型] [置信度] [限制数]"
    echo ""
    echo "类型: all, semantic, episode, procedural, preference, environment"
    echo "置信度: all, high, medium, low"
    exit 1
fi

echo "=== 记忆检索 ==="
echo "查询: $QUERY"
echo "类型: $TYPE"
echo "置信度: $CONFIDENCE"
echo "时间: $(date "+%Y-%m-%d %H:%M:%S CST")"
echo ""

# 构建搜索路径
SEARCH_DIRS=""
case "$TYPE" in
    semantic) SEARCH_DIRS="$MEM_BASE/semantic" ;;
    episode) SEARCH_DIRS="$MEM_BASE/episodes" ;;
    procedural) SEARCH_DIRS="$MEM_BASE/procedural" ;;
    preference) SEARCH_DIRS="$MEM_BASE/preferences" ;;
    environment) SEARCH_DIRS="$MEM_BASE/environment" ;;
    *) SEARCH_DIRS="$MEM_BASE/semantic $MEM_BASE/episodes $MEM_BASE/procedural $MEM_BASE/preferences $MEM_BASE/environment" ;;
esac

# 执行搜索
results=""
for dir in $SEARCH_DIRS; do
    if [ -d "$dir" ]; then
        found=$(grep -r "$QUERY" "$dir" --include="*.md" 2>/dev/null | grep -v "backup" | head -n "$LIMIT" || true)
        if [ -n "$found" ]; then
            results="$results$found"$'\n'
        fi
    fi
done

if [ -z "$(echo "$results" | tr -d '[:space:]')" ]; then
    echo "未找到相关记忆"
    exit 0
fi

echo "找到 $(echo "$results" | wc -l) 条结果:"
echo "---"

# 显示结果
echo "$results" | head -n "$LIMIT" | while IFS= read -r line; do
    file=$(echo "$line" | cut -d: -f1)
    content=$(echo "$line" | cut -d: -f2- | head -c 150)
    
    # 提取置信度
    conf=$(grep -i "confidence" "$file" 2>/dev/null | head -1 | sed 's/.*: *//' | tr -d ' ' || echo "unknown")
    
    # 提取来源
    src=$(grep -i "source" "$file" 2>/dev/null | head -1 | sed 's/.*: *//' | tr -d ' ' || echo "unknown")
    
    echo "📄 $(basename "$file" .md)"
    echo "   置信度: $conf | 来源: $src"
    echo "   $content..."
    echo ""
done

echo "---"
echo "检索完成"
