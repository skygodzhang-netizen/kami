# 任务：事件级剧情推演（scope=event）

扩写单事件纲：目标、人物、场景、桥段、篇末钩子、**章数分配理由**。

## 输入

- **卷号**：{{volume_num}}
- **事件 ID**：{{event_id}}
- **事件卡片**：{{event_card}}
- **事件级工坊**：{{workshop_event}}
- **卷级推演摘要**：{{plot_engine_volume_excerpt}}
- **角色现状**：{{character_status}}

## 输出要求

Markdown，含 YAML frontmatter：

```markdown
---
event_id: e01
volume: 1
title: 事件标题
estimated_chapters: 5
status: outlined
---

# 事件标题

## 事件目标
…

## 人物与场景
…

## 桥段节奏（篇内）
1. …

## 章数分配与理由
| 章 | 职能 | 情绪 | 理由 |
|----|------|------|------|
| 第1章 | 立局 | 紧张 | … |

## 篇末钩子
…

## 与下一事件衔接
…
```

- 章数分配表行数 = `estimated_chapters`
- 必须吸收工坊 `scene_beats`，可细化不可推翻卷级主线
- 不写正文，只写纲
