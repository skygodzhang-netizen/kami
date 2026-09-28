# 任务：事件级剧情工坊（scope=event）

为**单个事件/篇**生成场景节拍骨架与约束，服务后续 event_outline 扩写。

## 输入

- **卷号**：{{volume_num}}
- **事件 ID**：{{event_id}}
- **事件卡片**：{{event_card}}
- **卷情绪弧摘要**：{{volume_arc}}
- **卷级工坊约束**：{{volume_workshop_constraints}}
- **世界观爽点**：{{world_hooks}}

## 输出要求

输出 JSON：

```json
{
  "event_id": "e01",
  "title": "事件标题",
  "scene_beats": [
    {"order": 1, "scene": "场景名", "purpose": "情绪/信息目标", "trope": "桥段id"}
  ],
  "constraints": [
    "篇内必须…",
    "禁止…"
  ],
  "chapter_allocation_hints": [
    {"chapter_offset": 1, "focus": "立局", "emotion": "紧张"},
    {"chapter_offset": 2, "focus": "加压", "emotion": "愤怒"}
  ]
}
```

- `scene_beats` 3–7 条，覆盖入局→加压→转折→兑现→篇末钩
- `chapter_allocation_hints` 条数 ≈ `estimated_chapters`，说明每章职能
- 只输出 JSON
