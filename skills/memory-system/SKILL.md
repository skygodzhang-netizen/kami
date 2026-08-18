---
name: memory-system
description: Memory Intelligence Layer — 智能记忆系统，支持存储/检索/评估/维护/反思
---

# Memory Intelligence Layer

## 架构

```
  新信息
    ↓
 ┌─────────────┐
 │ Memory Judge │
 └──────┬──────┘
    ↓
 是否值得长期记忆？
    ↙️    ↘️
   否      是
    ↓      ↓
 Episode 自动分类
             ↓
 ┌─────────────────┐
 │ 去重 / 冲突检测  │
 └────────┬────────┘
          ↓
       Confidence
          ↓
     Memory Store
          ↓
    Retrieval Index
          ↓
      Agent 使用
```

## 核心脚本

### 1. Memory Judge — 质量评估与决策
```bash
bash ~/.openclaw/workspace/scripts/memory-judge-v2.sh '<内容>' [类型] [来源]
```
功能：
- 自动判断记忆类型 (semantic/episode/procedural/preference/environment)
- 去重检测
- 价值评分 (0-100)
- 置信度评估
- 存储决策

### 2. Memory Store — 智能存储
```bash
bash ~/.openclaw/workspace/scripts/memory-store-v2.sh <类型> <内容> [来源] [置信度] [标签]
```
元数据：
- `source`: manual / automated / system
- `confidence`: high / medium / low
- `created`: 创建时间
- `updated`: 最后更新时间
- `tags`: 标签列表
- `status`: active / archived

### 3. Memory Retrieve — 检索
```bash
bash ~/.openclaw/workspace/scripts/memory-retrieve-v2.sh <关键词> [类型] [置信度] [限制数]
```
过滤：
- 类型: all, semantic, episode, procedural, preference, environment
- 置信度: all, high, medium, low

### 4. Memory Index — 索引构建
```bash
bash ~/.openclaw/workspace/scripts/memory-index.sh
```
- 全文索引
- 加速检索

### 5. Memory Maintenance — 维护
```bash
bash ~/.openclaw/workspace/scripts/memory-maintenance-v2.sh [保留天数]
```
功能：
- 过期检测 (默认90天)
- 低置信度提醒
- 统计报告

### 6. Daily Reflection — 每日反思
```bash
bash ~/.openclaw/workspace/scripts/daily-reflection-v2.sh
```
生成：
- 今日事件回顾
- 模式分析
- 改进建议
- 保存到 reflections/YYYY-MM-DD.md

## 记忆结构

```
memory/
├── semantic/        # 事实记忆 (基础设施、技术栈)
├── episodes/        # 事件记忆 (今天做了什么)
├── procedural/      # 操作经验 (SOP、解决方案)
├── preferences/     # 用户偏好 (风格、决策倾向)
├── environment/     # 环境状态 (运行状态、历史故障)
├── reflections/     # 反思记录 (每日反思)
├── .index           # 检索索引
└── backup-*         # 自动备份
```

## 使用示例

### 存储用户偏好
```bash
bash ~/.openclaw/workspace/scripts/memory-store-v2.sh \
  "preference" \
  "用户喜欢台湾节点用于代理" \
  "manual" \
  "high" \
  "location,proxy"
```

### 检索记忆
```bash
bash ~/.openclaw/workspace/scripts/memory-retrieve-v2.sh \
  "台湾" "preference"
```

### 评估记忆质量
```bash
bash ~/.openclaw/workspace/scripts/memory-judge-v2.sh \
  "用户喜欢简洁回答" "preference" "manual"
```

### 每日反思
```bash
bash ~/.openclaw/workspace/scripts/daily-reflection-v2.sh
```

## 置信度模型

| 置信度 | 说明 | 更新策略 |
|--------|------|----------|
| high | 多次确认、用户明确表达 | 保守更新 |
| medium | 单次观察、可能有变化 | 定期验证 |
| low | 猜测、不确定的信息 | 快速过期 |

## 来源标记

| 来源 | 说明 | 可信度 |
|------|------|--------|
| manual | 用户手动输入 | 高 |
| automated | 系统自动记录 | 中 |
| system | 系统配置 | 高 |

---
*Memory Intelligence Layer v2.0*
