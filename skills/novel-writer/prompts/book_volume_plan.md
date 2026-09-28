# 任务：全书卷规划（Book Volume Plan）

规划全书 **N 卷**结构（N 可配置，默认参考 `total_volumes`，禁止写死 5×50）。

## 输入

- **书名**：{{book_title}}
- **题材**：{{genre}}
- **目标总字数**：{{target_words}}
- **规划卷数**：{{total_volumes}}
- **每卷章数参考**：{{chapters_per_volume_hint}}
- **世界观爽点**：{{world_hooks}}

## 每卷须包含

| 字段 | 说明 |
|------|------|
| title | 卷名 |
| target_words | 本卷目标字数 |
| protagonist_state_start | 主角卷初状态 |
| protagonist_state_end | 主角卷末状态 |
| main_location | 主活动区域 |
| core_conflict | 卷级核心矛盾 |
| estimated_chapters | 预估章数（可变） |
| chapter_range | start/end 全局章号 |
| volume_hook | 卷末钩子 |

## 输出

### 第一部分：Markdown 摘要

全书一句话卖点 + 五卷（或 N 卷）情绪递进说明。

### 第二部分：JSON（必须，放 ```json 代码块）

```json
{
  "book_title": "书名",
  "total_volumes": 5,
  "target_words": 1000000,
  "book_core_conflict": "全书核心矛盾",
  "volumes": [
    {
      "volume": 1,
      "title": "卷名",
      "target_words": 200000,
      "protagonist_state_start": "…",
      "protagonist_state_end": "…",
      "main_location": "…",
      "core_conflict": "…",
      "estimated_chapters": 40,
      "chapter_range": {"start": 1, "end": 40},
      "volume_hook": "…"
    }
  ]
}
```

要求：

- 各卷 `chapter_range` 连续无重叠，覆盖从第 1 章起
- 卷间主角状态首尾衔接
- 只输出规划，不写正文
