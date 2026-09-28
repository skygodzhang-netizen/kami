# 任务：卷级剧情工坊（scope=volume）

为**整卷**生成事件/篇卡片骨架（桥段类型组合），不展开单章细节。

## 输入

- **卷号**：{{volume_num}}
- **卷情绪弧**：{{volume_arc}}
- **世界观爽点**：{{world_hooks}}
- **事件章数范围**：{{event_chapters_min}}–{{event_chapters_max}} 章/事件
- **本卷事件数量建议**：{{events_per_volume}}
- **桥段库参考**（规则工坊已预选）：{{workshop_volume_stub}}

## 输出要求

输出 JSON（可包在 ```json 代码块内），结构：

```json
{
  "volume": 1,
  "event_cards": [
    {
      "event_id": "e01",
      "title": "事件标题",
      "trope_ids": ["misunderstanding_reversal", "faction_pressure"],
      "trope_rationale": "为何此组合服务本卷情绪",
      "estimated_chapters": 5,
      "protagonist_state_start": "卷初状态",
      "protagonist_state_end": "篇末状态",
      "location": "主活动区域",
      "hook_to_next": "通往下一事件的衔接",
      "emotion_arc": "屈辱→愤怒→小胜"
    }
  ],
  "volume_emotion_line": "卷内整体情绪走势一句话",
  "constraints": ["本卷禁止…", "必须出现…"]
}
```

规则：

- `event_id` 连续：e01, e02, …
- 每事件 `estimated_chapters` 须在配置范围内
- 事件顺序须形成完整卷弧，末事件留卷间钩子
- 只输出 JSON，不要写正文
