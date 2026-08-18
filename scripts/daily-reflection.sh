#!/bin/bash
# daily-reflection.sh — 每日反思脚本
# 生成每日反思报告，发现改进点

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
DATE=$(date +%Y-%m-%d)
TODAY_EPISODE="$MEM_BASE/episodes/$DATE.md"
REFLECTION="$MEM_BASE/reflections/$DATE.md"

mkdir -p "$MEM_BASE/reflections"

echo "=== 每日反思 ==="
echo "日期: $DATE"
echo ""

# 检查今日 episode
if [ ! -f "$TODAY_EPISODE" ]; then
    echo "⚠️  今日暂无记录"
    exit 0
fi

echo "📝 今日记录:"
cat "$TODAY_EPISODE" | head -20
echo ""

echo "🤔 反思要点:"
echo "  1. 今天解决了什么问题?"
echo "  2. 有什么重复出现的模式?"
echo "  3. 哪些操作可以自动化?"
echo "  4. 哪些记忆需要更新?"
echo "  5. 有哪些错误应该避免?"
echo ""

echo "💡 建议:"
echo "  - 检查 incidents.md 是否有新增故障"
echo "  - 更新 environment/status.md 状态"
echo "  - 考虑创建新的 Skill"
echo ""

echo "✅ 反思完成"
