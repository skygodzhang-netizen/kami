#!/bin/bash
# memory-loader.sh — 分层记忆系统加载器
MEM_BASE="$HOME/.openclaw/workspace/memory"

echo "=== 记忆系统状态 ==="
for f in semantic/infrastructure.md environment/status.md preferences/user-profile.md procedural/sop.md preferences/user-model.md; do
    if [ -f "$MEM_BASE/$f" ]; then
        echo "✅ $f"
    else
        echo "❌ $f (缺失)"
    fi
done
echo "记忆系统就绪"
