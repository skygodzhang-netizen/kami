# 任务：卷级剧情推演（scope=volume）

基于卷情绪弧与卷级工坊卡片，生成**可落盘**的卷内事件规划。

## 输入

- **卷号**：{{volume_num}}
- **卷情绪弧**：{{volume_arc}}
- **世界观爽点**：{{world_hooks}}
- **卷级工坊结果**：{{workshop_volume}}
- **章数配置**：每事件 {{event_chapters_min}}–{{event_chapters_max}} 章；本卷可选上限 {{chapters_per_volume}}

## 推演要求

1. 确定事件顺序与每事件预估章数（可变，须写明理由）
2. 卷内情绪线：低开→抬升→高潮→卷末钩子
3. 事件间衔接：每事件 `hook_to_next` 须具体可写
4. 主角卷内状态递进：首事件 `protagonist_state_start` → 末事件 `protagonist_state_end`

## 输出格式

### 第一部分：自然语言（Markdown）

#### 卷内情绪线
用 3–5 句描述卷内读者情绪曲线。

#### 事件顺序与章数理由
逐事件说明为何分配 N 章。

### 第二部分：机器可读 JSON（必须）

```json
{
  "volume": 1,
  "title": "第1卷标题",
  "volume_emotion_line": "…",
  "events": [
    {
      "event_id": "e01",
      "volume": 1,
      "title": "…",
      "trope_ids": ["…"],
      "estimated_chapters": 5,
      "actual_chapters": 0,
      "protagonist_state_start": "…",
      "protagonist_state_end": "…",
      "location": "…",
      "hook_to_next": "…",
      "status": "planned"
    }
  ],
  "transitions": [
    {"from": "e01", "to": "e02", "bridge": "…"}
  ]
}
```

`start_chapter` 由系统根据卷号与章数自动计算，可不填。
