#!/bin/bash
# daily-reflection-v2.sh — 每日反思系统
# 生成反思报告和改进建议

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
DATE=$(date +%Y-%m-%d)
TODAY_EPISODE="$MEM_BASE/episodes/$DATE.md"
REFLECTION_DIR="$MEM_BASE/reflections"
mkdir -p "$REFLECTION_DIR"
REFLECTION_FILE="$REFLECTION_DIR/$DATE.md"

echo "=== 每日反思 ==="
echo "日期: $DATE"
echo ""

# 1. 回顾今日事件
echo "📝 今日事件回顾:"
if [ -f "$TODAY_EPISODE" ]; then
    today_count=$(grep -c "^##" "$TODAY_EPISODE" 2>/dev/null || echo 0)
    echo "  - 记录事项: $today_count 条"
    head -30 "$TODAY_EPISODE"
else
    echo "  - 今日暂无记录"
fi
echo ""

# 2. 检索历史相似事件
echo "🔍 历史相似事件:"
recent_episodes=$(find "$MEM_BASE/episodes" -name "*.md" -mtime -7 | wc -l)
echo "  - 近7天 episode 数量: $recent_episodes"

# 查找常见模式
echo ""
echo "📊 模式分析:"
if [ -f "$MEM_BASE/episodes" ]; then
    # 统计故障类型
    fault_count=$(grep -r "故障\|异常\|错误\|崩溃" "$MEM_BASE/episodes" --include="*.md" 2>/dev/null | wc -l || echo 0)
    echo "  - 故障记录: $fault_count 条"
fi
echo ""

# 3. 生成反思问题
echo "🤔 反思问题:"
echo "  1. 今天解决了什么问题?"
echo "  2. 有什么重复出现的模式?"
echo "  3. 哪些操作可以自动化?"
echo "  4. 哪些记忆需要更新?"
echo "  5. 有哪些错误应该避免?"
echo ""

# 4. 生成建议
echo "💡 改进建议:"
echo "  - 检查 incidents.md 是否有新增故障"
echo "  - 更新 environment/status.md 状态"
echo "  - 考虑创建新的 Skill 自动化重复任务"
echo "  - 验证低置信度记忆"
echo ""

# 5. 写入反思记录
cat > "$REFLECTION_FILE" << EOF
# 每日反思 - $DATE

## 事件回顾
$(if [ -f "$TODAY_EPISODE" ]; then head -20 "$TODAY_EPISODE"; else echo "无记录"; fi)

## 模式分析
- 近7天 episode 数量: $recent_episodes

## 改进建议
1. 检查故障记录
2. 更新环境状态
3. 考虑自动化重复任务
4. 验证低置信度记忆

---
*由 daily-reflection-v2.sh 自动生成*
EOF

echo "✅ 反思完成，已保存到: $REFLECTION_FILE"
