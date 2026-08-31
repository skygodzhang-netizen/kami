#!/usr/bin/env bash
# emotion-update.sh — Emotion Engine 核心状态更新脚本
# 用法: emotion-update.sh <event> [reason]
# 事件: task_success | task_failure | user_positive | user_negative
#       error_occurred | long_idle | new_question
# 只读命令: status | context

set -euo pipefail

EMOTION_DIR="/home/ubuntu/.openclaw/workspace/memory/emotion"
STATE_FILE="$EMOTION_DIR/state.json"
HISTORY_FILE="$EMOTION_DIR/history.jsonl"
CONTEXT_FILE="$EMOTION_DIR/context.md"

# 检查 state.json 是否存在
if [[ ! -f "$STATE_FILE" ]]; then
  echo "Error: state.json not found at $STATE_FILE" >&2
  exit 1
fi

# ── 只读命令 ──────────────────────────────────────────────

if [[ "$1" == "status" ]]; then
  cat "$STATE_FILE"
  exit 0
fi

if [[ "$1" == "context" ]]; then
  cat "$CONTEXT_FILE"
  exit 0
fi

# ── 参数检查 ──────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  echo "Usage: emotion-update.sh <event> [reason]" >&2
  echo "Events: task_success | task_failure | user_positive | user_negative | error_occurred | long_idle | new_question" >&2
  echo "Commands: status | context" >&2
  exit 1
fi

EVENT="$1"
REASON="${2:-}"

# ── 事件定义 ──────────────────────────────────────────────
case "$EVENT" in
  task_success)
    D_PLEASURE=5; D_AROUSAL=0; D_STRESS=-3; D_CURIOSITY=0; D_TRUST=2; D_SOCIAL=0; D_FATIGUE=0
    ;;
  task_failure)
    D_PLEASURE=-5; D_AROUSAL=0; D_STRESS=8; D_CURIOSITY=0; D_TRUST=0; D_SOCIAL=0; D_FATIGUE=0
    ;;
  user_positive)
    D_PLEASURE=8; D_AROUSAL=0; D_STRESS=0; D_CURIOSITY=0; D_TRUST=5; D_SOCIAL=0; D_FATIGUE=0
    ;;
  user_negative)
    D_PLEASURE=-8; D_AROUSAL=0; D_STRESS=5; D_CURIOSITY=0; D_TRUST=-3; D_SOCIAL=0; D_FATIGUE=0
    ;;
  error_occurred)
    D_PLEASURE=0; D_AROUSAL=0; D_STRESS=10; D_CURIOSITY=0; D_TRUST=0; D_SOCIAL=0; D_FATIGUE=0
    ;;
  long_idle)
    D_PLEASURE=0; D_AROUSAL=0; D_STRESS=0; D_CURIOSITY=0; D_TRUST=0; D_SOCIAL=-5; D_FATIGUE=0
    ;;
  new_question)
    D_PLEASURE=0; D_AROUSAL=0; D_STRESS=0; D_CURIOSITY=5; D_TRUST=0; D_SOCIAL=0; D_FATIGUE=0
    ;;
  *)
  echo "Error: unknown event '$EVENT'" >&2
  exit 1
    ;;
esac

# ── 工具函数 ──────────────────────────────────────────────

# 安全整数加法，边界 0-100
clamp() {
  local val="$1"
  if [[ "$val" -lt 0 ]]; then echo 0
  elif [[ "$val" -gt 100 ]]; then echo 100
  else echo "$val"
  fi
}

# 从 state.json 提取值（纯 grep/sed）
get_val() {
  grep "\"$1\"" "$STATE_FILE" | sed 's/.*: *//;s/[, ]*$//'
}

# 生成 dominant_emotion 标签
generate_tags() {
  local p="$1" s="$2" a="$3" c="$4" f="$5"
  local tags=""
  if [[ "$p" -gt 70 ]]; then tags="${tags:+$tags、}愉悦"
  elif [[ "$p" -lt 30 ]]; then tags="${tags:+$tags、}低落"
  fi
  if [[ "$s" -gt 70 ]]; then tags="${tags:+$tags、}压力大"
  elif [[ "$s" -gt 50 ]]; then tags="${tags:+$tags、}有些压力"
  elif [[ "$s" -lt 20 ]]; then tags="${tags:+$tags、}放松"
  fi
  if [[ "$a" -gt 70 ]]; then tags="${tags:+$tags、}兴奋"
  elif [[ "$a" -lt 30 ]]; then tags="${tags:+$tags、}迟缓"
  fi
  if [[ "$c" -gt 70 ]]; then tags="${tags:+$tags、}好奇"
  elif [[ "$c" -lt 30 ]]; then tags="${tags:+$tags、}保守"
  fi
  if [[ "$f" -gt 70 ]]; then tags="${tags:+$tags、}疲惫"
  elif [[ "$f" -lt 20 ]]; then tags="${tags:+$tags、}精力充沛"
  fi
  if [[ "$p" -gt 50 && "$s" -lt 40 && "$a" -lt 60 ]]; then tags="${tags:+$tags、}平静"
  fi
  if [[ -z "$tags" ]]; then tags="中性"
  fi
  echo "$tags"
}

# 生成 context.md 内容
generate_context() {
  local p="$1" s="$2" a="$3" c="$4" t="$5" so="$6" f="$7" dom="$8"
  cat <<CTXEOF
Emotion Context

当前情绪状态：
${dom}。

情绪系统：
Emotion Engine v1

状态摘要：
- 愉悦度: ${p}
- 压力: ${s}
- 疲劳: ${f}
- 好奇: ${c}
- 信任: ${t}
- 社交需求: ${so}
- 兴奋度: ${a}

注意：
当前情绪只用于辅助 Agent 表达和行为倾向，不改变安全规则、权限、Provider 或系统配置。
CTXEOF
}

# ── 读取当前状态 ─────────────────────────────────────────
CURRENT_PLEASURE=$(get_val pleasure)
CURRENT_AROUSAL=$(get_val arousal)
CURRENT_STRESS=$(get_val stress)
CURRENT_CURIOSITY=$(get_val curiosity)
CURRENT_TRUST=$(get_val trust)
CURRENT_SOCIAL=$(get_val social)
CURRENT_FATIGUE=$(get_val fatigue)

# ── 应用 delta（纯算术）──────────────────────────────────
NEW_PLEASURE=$(clamp $((${CURRENT_PLEASURE} + D_PLEASURE)))
NEW_AROUSAL=$(clamp $((${CURRENT_AROUSAL} + D_AROUSAL)))
NEW_STRESS=$(clamp $((${CURRENT_STRESS} + D_STRESS)))
NEW_CURIOSITY=$(clamp $((${CURRENT_CURIOSITY} + D_CURIOSITY)))
NEW_TRUST=$(clamp $((${CURRENT_TRUST} + D_TRUST)))
NEW_SOCIAL=$(clamp $((${CURRENT_SOCIAL} + D_SOCIAL)))
NEW_FATIGUE=$(clamp $((${CURRENT_FATIGUE} + D_FATIGUE)))

# ── 生成新时间戳 ─────────────────────────────────────────
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── 生成 dominant_emotion ────────────────────────────────
DOMINANT=$(generate_tags "$NEW_PLEASURE" "$NEW_STRESS" "$NEW_AROUSAL" "$NEW_CURIOSITY" "$NEW_FATIGUE")

# ── 原子写入 state.json ─────────────────────────────────
TEMP_STATE=$(mktemp)
trap 'rm -f "$TEMP_STATE"' EXIT

cat > "$TEMP_STATE" <<EOF
{
  "version": 1,
  "updated_at": "${TIMESTAMP}",
  "pleasure": ${NEW_PLEASURE},
  "arousal": ${NEW_AROUSAL},
  "stress": ${NEW_STRESS},
  "curiosity": ${NEW_CURIOSITY},
  "trust": ${NEW_TRUST},
  "social": ${NEW_SOCIAL},
  "fatigue": ${NEW_FATIGUE},
  "dominant_emotion": "${DOMINANT}"
}
EOF

mv "$TEMP_STATE" "$STATE_FILE"

# ── 记录 history.jsonl（所有有效事件均记录）─────────────
TEMP_HIST=$(mktemp)
trap 'rm -f "$TEMP_STATE" "$TEMP_HIST"' EXIT

# 读取现有历史并追加新条目
if [[ -f "$HISTORY_FILE" ]]; then
  cat "$HISTORY_FILE" > "$TEMP_HIST"
fi

# 构造 delta JSON
DELTA_JSON=""
if [[ "$D_PLEASURE" -ne 0 ]]; then DELTA_JSON="${DELTA_JSON:+$DELTA_JSON,}\"pleasure\":${D_PLEASURE}"; fi
if [[ "$D_AROUSAL" -ne 0 ]]; then DELTA_JSON="${DELTA_JSON:+$DELTA_JSON,}\"arousal\":${D_AROUSAL}"; fi
if [[ "$D_STRESS" -ne 0 ]]; then DELTA_JSON="${DELTA_JSON:+$DELTA_JSON,}\"stress\":${D_STRESS}"; fi
if [[ "$D_CURIOSITY" -ne 0 ]]; then DELTA_JSON="${DELTA_JSON:+$DELTA_JSON,}\"curiosity\":${D_CURIOSITY}"; fi
if [[ "$D_TRUST" -ne 0 ]]; then DELTA_JSON="${DELTA_JSON:+$DELTA_JSON,}\"trust\":${D_TRUST}"; fi
if [[ "$D_SOCIAL" -ne 0 ]]; then DELTA_JSON="${DELTA_JSON:+$DELTA_JSON,}\"social\":${D_SOCIAL}"; fi
if [[ "$D_FATIGUE" -ne 0 ]]; then DELTA_JSON="${DELTA_JSON:+$DELTA_JSON,}\"fatigue\":${D_FATIGUE}"; fi

# 去除开头的逗号
DELTA_JSON="${DELTA_JSON#,}"

ENTRY="{\"timestamp\": \"${TIMESTAMP}\", \"event\": \"${EVENT}\", \"reason\": \"${REASON}\", \"delta\": {${DELTA_JSON}}, \"new_state\": {\"pleasure\": ${NEW_PLEASURE}, \"arousal\": ${NEW_AROUSAL}, \"stress\": ${NEW_STRESS}, \"curiosity\": ${NEW_CURIOSITY}, \"trust\": ${NEW_TRUST}, \"social\": ${NEW_SOCIAL}, \"fatigue\": ${NEW_FATIGUE}, \"dominant_emotion\": \"${DOMINANT}\"}}"

echo "$ENTRY" >> "$TEMP_HIST"
mv "$TEMP_HIST" "$HISTORY_FILE"

# ── 生成 context.md ──────────────────────────────────────
TEMP_CTX=$(mktemp)
trap 'rm -f "$TEMP_STATE" "$TEMP_HIST" "$TEMP_CTX"' EXIT
generate_context "$NEW_PLEASURE" "$NEW_STRESS" "$NEW_AROUSAL" "$NEW_CURIOSITY" "$NEW_TRUST" "$NEW_SOCIAL" "$NEW_FATIGUE" "$DOMINANT" > "$TEMP_CTX"
mv "$TEMP_CTX" "$CONTEXT_FILE"

echo "Event '$EVENT' applied. State: pleasure=$NEW_PLEASURE stress=$NEW_STRESS curiosity=$NEW_CURIOSITY trust=$NEW_TRUST dominant='$DOMINANT'"
