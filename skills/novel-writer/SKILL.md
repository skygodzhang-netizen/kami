---
name: novel-writer
description: 长篇网文 Agent 创作技能 v3.0 — 卷/事件/章四层编排、产物驱动流水线、Pre-Init 创意门禁、作者签名跨题材复用
version: 3.0.0
author: 梁青春
license: MIT
homepage: https://github.com/LuckLiang/novel-writer
platforms: [macos, linux, windows]
metadata: {"openclaw":{"emoji":"📖","homepage":"https://github.com/LuckLiang/novel-writer","requires":{"anyBins":["python","python3","py"]}},"hermes":{"tags":["Creative","Writing","Fiction","Chinese","Novel","Long-form","Web-fiction"],"related_skills":[]}}
---

# Novel Writer - 自动化小说创作系统

## OpenClaw 生产边界（本地适配；非上游原文）

- 每次脚本调用显式设置 `run_dir` 为 `/home/ubuntu/.openclaw/workspace/novels/<book>/` 下的当前小说项目。不要省略参数，不要使用默认全局目录。
- 世界观、人物、章节摘要、时间线与伏笔只写当前小说项目目录。OpenClaw main/ops Memory、全局 SOUL/AGENTS/USER、Agnes Provider、模型路由均不得由本技能修改。
- Agent 可自主创建、维护和改进可复用 Skill。先查现有能力；新 Skill 在 workshop 验证语法、discovery、职责、触发冲突、功能、回归和安全边界后，才视为生产可用。不得仅因 Agent 自建而隔离。创建 Skill 不授权修改 CLI Provider、第二套小说记忆或无关生产配置。
- 先完成规划与连续性门禁，再写 RAW；后处理保留 RAW、候选与终稿。再次定稿同一章时核对项目进度及字数，避免重复累计。


> ⚠️ **创作声明 / Philosophy**
>
> **人类的情感是写作的灵魂，AI 只是工具。**
>
> 本技能用于辅助结构规划、设定一致性与产出效率，**不能**也**不应**被指望单独写出真正的文学巨作。
> 打动人心的故事来自你的生活阅历、情感体验与审美判断——这些只能由**你**注入。
> 请把 AI 当作协作者与磨刀石，而非代笔者。

**版本 Version**: 3.0.0 \
**最后更新 Updated**: 2026-06-25 \
**核心特性**: 卷→事件→章四层节拍器、事件可变章数、卷级/事件级编排（Phase 1）、章级剧情工坊/推演默认关闭、章节流程、Pre-Init门禁

## Hermes 运行模式 / Hermes Runtime

在 Hermes 中，本技能以 **流程指令 + 产物落盘** 为主，不依赖 OpenClaw 的 `run_skill` API。

### 安装

```bash
hermes skills install git:LuckLiang/novel-writer@main
# ClawHub 发布后也可：
hermes skills install @luckliang/novel-writer
```

### 技能目录与脚本路径

安装后 Agent 会暴露技能根目录。引用 bundled 资源时使用：

| 平台 | 路径变量 |
|------|----------|
| Hermes | `${HERMES_SKILL_DIR}/scripts/...`、`${HERMES_SKILL_DIR}/prompts/...` |
| OpenClaw | `{baseDir}/scripts/...`、`{baseDir}/prompts/...` |

### 执行原则（Hermes）

1. 由 **Agent 本人**按本 SKILL 主链执行：`init` → `world_hooks` → `voice_config` → 规划 → 写作 → `finalize_chapter`
2. 各阶段读取 `prompts/*.md` 作为指令模板，产物写入用户项目的 `config/`、`planning/`、`plot_engine/`、`final/`
3. 修改 `workflow_state.json` 等 JSON 时，用 Python 完整重建，**禁止**用 patch 直接改 `notes` 字段
4. `scripts/openclaw_entry.py` 仅在 OpenClaw 注入 `model_callable` 时使用；Hermes 下**不要**依赖其 LLM action

### 触发方式

- 斜杠命令：`/novel-writer`
- 自然语言：「用 novel-writer 帮我规划第一卷的事件结构」

## 系统概览 / System Overview

Novel Writer 现在采用分阶段产物链路驱动写作，核心上游已接通：

```text
plot_workshop -> plot_engine -> outline -> draft
```

完整创作主链（v3.0）：

```text
init
-> world_hooks
-> voice_config
-> plan_book_volumes              # 全书 N 卷规划（可选门禁）
-> volume_arc                      # 当前卷
-> plot_workshop(scope=volume) -> plot_engine(scope=volume)
-> [用户确认]
-> 对当前 event：
     plot_workshop(scope=event)
  -> plot_engine(scope=event)       # event_outline 落盘
  -> chapter_beats(event_id)
  -> write_chapter(outline/draft/finalize)
```

便捷封装：`plan_volume_events(pipeline=True)` = 卷工坊 → 卷推演；`plan_event(pipeline=True)` = 事件工坊 → 事件推演。

**章级 plot_workshop / plot_engine 默认关闭**（`plot_workshop_per_chapter_enabled=false`，`plot_engine_per_chapter_enabled=false`）。仅在复杂章或用户显式开启 config 后使用，**不是默认主链**。

### 四层节拍器 / 何时生成哪一层

| 层级 | 产物 | Action | 说明 |
|------|------|--------|------|
| 全书 | `planning/book_volume_plan.md` + `.json` | `plan_book_volumes` | 卷名、字数、主角卷初/末、区域、矛盾 |
| 卷 | `planning/volume_{n}/volume_event_plan.json` | `plan_volume_events` | 卷内事件卡片列表 |
| 事件/篇 | `planning/volume_{n}/events/event_{id}_outline.md` | `plan_event` | 单事件纲 + 章数分配建议 |
| 章 | `plot_engine/chapter_beats_{start}-{end}.md` | `chapter_beats(event_id)` | **仅**当前事件的 N 章 |

⚠️ `chapter_beats` **禁止**在未生成 `event_outline` 时为整卷批量生成（有 `volume_event_plan` 时强制 `event_id`）。

### Legacy 模式

- 无 `volume_event_plan.json`：`chapter_beats` 仍可按章号写作，preflight 不强制事件层
- 无 `book_volume_plan`：卷章区间回退 `chapters_per_volume`（默认 50）
- `require_book_volume_plan_at_pre_init=false`（默认）：Pre-Init 不强制全书规划

⚠️ **重要例外——全新项目需走 Pre-Init Creative Workflow**
> 当用户启动一本**全新小说**（非续写已有项目），切忌直接 init 跳过创意咨询。必须先走下面的前置流程。

### Pre-Init Creative Workflow / 创意咨询前置流程（全新项目专用）

#### 适用场景
- 用户想"写一本新小说"，但没有成型的设定
- 用户提供了开篇灵感/片断/概念，需要展开为完整大纲
- 用户不确定书名、风格方向

#### 流程（严禁跳过环节）

**Phase 1 — 概念设计草案**
1. 解读用户提供的开篇/灵感素材，提炼核心设定（人物、冲突、风格）
2. 设计初步方案：人物定位、故事框架（3-4卷）、核心卖点/爽点、对标作品
3. 呈现方案：一次性呈现完整概念（人物标签表、卷节拍概览、核心看点清单）
4. 等待用户反馈——用户会指出方向是否对味（"太老套""太圆""没冲突感"等）

**Phase 2 — 迭代优化**
5. 根据用户反馈重新设计，不修补旧方案，直接重写
   - 如果用户说"对标某某作品"——研究该作品特色并融入结构设计
   - 如果用户补充角色细节（如"装老年痴呆的陈爷""阿福管家"）——纳入并强化其特质
6. 重复提交-反馈-重写循环，直到用户说"方向对了"
7. 确认关键设定：书名（建议2-4个选项）、字数体量、章节估算、文件夹拼音缩写

**Phase 3 — 全章节拍表设计**
8. 设计完整章节节拍表（chapter_beats），逐章编写：核心事件、笑点/爆点、章末钩子、字数估算
   - 标注⭐级名场面位置
   - 标注贯穿角色的串场节点
   - 标注核心人物关系递进节点
   - 保证每章有实质性事件推进，零过渡章
9. 等待用户确认节奏——用户可能会要求合并章节、增加爆点密度
10. 按反馈调整节拍表，确保整条情绪曲线合理

**Phase 4 — 确认后执行 Init**
11. 仅当用户明确确认节拍表无误后，执行 `confirm_pre_init`，再执行 `init`：
    - 清理旧版本节拍表文件，仅保留确认版
    - 创建完整项目目录结构（见下方「标准目录布局」）
    - 生成 `config/novel_writer_config.json`（含反套路规则：禁止默认爱情线/真相大白/正义胜利）
    - 生成 `config/workflow_state.json`
    - 生成 `config/voice_config.json`（含角色约束规则、禁止要素、对话风格标签）
    - 生成 `config/character_cards.json`（含所有角色设定、重要关系映射）
    - 生成 `config/creative_workflow.json`（Pre-Init 进度）
    - 生成 `world_hooks.md`（爽点类型预埋、情绪锚点分章标注）
    - 生成 `config/progress.json`
    - 将确认后的节拍表写入 `plot_engine/chapter_beats.md`
12. 汇报完整目录结构 + 配置摘要，正式进入创作链

#### 关键反套路原则（基于实战经验）

| 原则 | 说明 |
|------|------|
| 不默认写爱情线 | 男女主角可以是战友情/信任关系，禁止无脑配对 |
| 不默认真相大白 | 开放式结局往往比强行摊牌更有余韵 |
| 不默认正义胜利 | 荒诞喜剧中"不了了之"也是好结局 |
| 需要贯穿角色 | 一个出现在全篇多个节点的角色，能增强结构感（如老疤从监狱到小卖部） |
| 配角需要有隐藏深度 | 如"装老年痴呆的老江湖""沉默管家的黑活能力" |
| 每章必须有实质性事件 | 零过渡章，每章有核心冲突或信息增量 |
| 信息差是核心引擎 | 读者知道真相，角色各自脑补——双重笑料来源 |
| 先出节拍表再 init | 全章节拍表是项目的"地基"，须先确认再建楼 |
| 章节命名随内容独立设计 | 不要求统一格式，每章标题暗示本章核心矛盾或名场面 |

系统特点：

- 前置产物全部会落盘，不再只返回文本
- `ConfigManager.get_context_snapshot()` 会自动回收上游产物并补齐写作上下文
- 大纲与草稿阶段都会吸收剧情工坊结果和剧情推演结果
- 草稿阶段会额外注入关系摘要、阵营摘要、隐藏人味计划
- 终稿入库后自动触发角色同步、关系一致性检查、剧情推荐

## 标准目录布局 / Project Layout（v3.0.0）

```text
{project_root}/
├── config/
│   ├── novel_writer_config.json   # 含 total_volumes, event_chapters_min/max, 章级工坊开关
│   ├── progress.json
│   ├── workflow_state.json
│   ├── voice_config.json
│   ├── character_cards.json
│   ├── creative_workflow.json
│   └── author_profile.json      # 作者签名（per-author，可跨项目复用）
├── planning/
│   ├── book_volume_plan.md        # Phase 3
│   └── volume_{n}/
│       ├── volume_outline.md
│       ├── volume_event_plan.json
│       └── events/
│           └── event_{id}_outline.md
├── plot_engine/
│   ├── chapter_beats_{start}-{end}.md   # 按事件生成
│   ├── plot_workshop_chapter_{n}.json   # 可选，默认不用
│   └── plot_engine_chapter_{n}.md
├── final/
│   └── chapter-{n}-final.md
├── world_hooks.md
└── volume_arc.md
```

启动时会自动将旧版根目录文件迁移至上述结构。

## 数据状态机 / ProjectState（v2.1.0）

`ProjectState` 是 novel-writer 的内建状态管理引擎，解决「写完一章后配置文件不同步」的根本问题。

### 自动同步流程

```
finalize_chapter 执行时，ProjectState 自动执行：
  1. 加载所有配置文件 → 内存快照
  2. ChapterDiff 分析终稿文本 → 检测变化
     ├─ 修为突破（正则匹配）
     ├─ 物品获得（引号内检测）
     ├─ 新角色登场（首次出现角色名）
     └─ 关键事件（系统提示+章末钩子）
  3. 同步到配置文件
     ├─ workflow_state.json → 添加章记录 + 更新 current_chapter
     ├─ character_cards.json → 更新修为 + 新增角色
     └─ novel_writer_config.json → 更新 current_chapter + power_level
  4. 触发 after_finalize 钩子
```

### 生命周期钩子系统

创作流程中的关键节点可注册钩子，消除"检查类"子技能的手动调用：

| 钩子事件 | 触发时机 | 原来对应的子技能 |
|----------|---------|-----------------|
| `before_outline` | 写大纲前 | novel-writer-advanced（配置检查）, novel-pre-writing-state-sync |
| `after_draft` | 草稿生成后 | novel-chapter-drafting-quality, novel-chapter-expansion-techniques |
| `before_finalize` | 终稿入库前 | novel-chapter-scope-correction |
| `after_finalize` | 终稿入库后 | novel-post-chapter-state-sync, character-card-maintenance |
| `after_volume` | 卷完结 | manuscript-three-review-three-proof, novel-project-health-audit |

向 ProjectState 注册钩子：

```python
ps = ProjectState(project_root)
ps.register_hook("after_draft", my_word_count_check)
ps.register_hook("after_finalize", my_custom_sync)
ps.trigger("after_draft", chapter_num=ch, content=draft_text)
```

## 支持的 Actions

### 核心创作流程

| Action | 功能 | 必需参数 |
|--------|------|----------|
| `confirm_pre_init` | 确认 Pre-Init 完成，解锁 init | - |
| `init` | 初始化项目（新 projects 须先 confirm_pre_init；续写可用 `force=True`） | - |
| `world_hooks` | 生成世界观爽点预埋（结构按题材） | `genre`, `core_pleasure`（可配置，默认「未指定」） |
| `voice_config` | 生成声音配置（merge `author_profile` 签名） | `world_hooks`, `genre` |
| `plan_book_volumes` | 全书卷规划（`use_llm=False` 可规则桩） | `target_words`, `total_volumes` |
| `volume_arc` | 设计卷情绪弧 | `world_hooks`, `target_words` |
| `plan_volume_events` | 卷内事件清单；`pipeline=True` 走工坊+推演 | `volume_num`, `pipeline` |
| `plan_event` | 单事件纲；`pipeline=True` 走工坊+推演 | `volume_num`, `event_id`, `pipeline` |
| `chapter_beats` | 生成**本事件**章节节拍表 | `volume_num`, `event_id`, `start_chapter` |
| `plot_workshop` | 桥段骨架：`scope=volume|event`（主链）；`scope=chapter` 默认关闭 | `scope`, `volume_num`, `event_id` |
| `plot_engine` | 剧情推演：`scope=volume|event`（主链）；`scope=chapter` 默认关闭 | `scope`, `volume_num`, `event_id` |
| `write_chapter` | 执行单章写作流程 | `chapter_num`, `stage` |
| `confirm_step` | 确认大纲或草稿 | `chapter_num`, `step` |
| `finalize_chapter` | 终稿入库并触发后续流程（含ProjectState自动同步） | `chapter_num` |
| `workflow_audit` | 审计前置文件与章节流程 | - |

### 多卷管理

| Action | 功能 | 必需参数 |
|--------|------|----------|
| `check_volume_completion` | 检查卷完成（联动 book_plan / event_plan 章号区间） | `chapter_num` |
| `transition_volume` | 流转下一卷 + 输出事件编排清单 | `current_volume` |

### 角色卡管理

| Action | 功能 | 必需参数 |
|--------|------|----------|
| `get_character` | 获取角色信息 | `character_id` |
| `update_character` | 更新角色信息 | `character_id`, `character_data` |
| `list_characters` | 列出所有角色 | - |
| `validate_characters` | 检查角色一致性 | `chapter_num` |

### 角色关系管理

| Action | 功能 | 必需参数 |
|--------|------|----------|
| `create_relationship` | 创建角色关系 | `character_a`, `character_b`, `rel_type` |
| `update_relationship` | 更新关系状态 | `character_a`, `character_b` |
| `get_relationship` | 查询关系 | `character_a`, `character_b` |
| `list_relationships` | 列出关系 | - |
| `delete_relationship` | 删除关系 | `character_a`, `character_b` |
| `get_character_relationships` | 获取角色所有关系 | `character_id` |
| `get_relationship_network` | 获取关系网络 | - |
| `create_faction` | 创建阵营 | `name`, `faction_type` |
| `get_faction` | 查询阵营 | `faction_id` |
| `list_factions` | 列出阵营 | - |
| `add_faction_member` | 添加阵营成员 | `faction_id`, `character_id` |
| `validate_relationships` | 关系一致性检查 | `chapter_num` |
| `detect_conflicts` | 检测关系冲突 | - |
| `recommend_plot` | 生成剧情推荐 | `chapter_num` |
| `generate_scene_outline` | 生成场景大纲 | `recommendation` |

## 产物与回灌 / Artifacts and Context Recovery

### 自动落盘产物

| Action | 产物 |
|--------|------|
| `init` | `novel_writer_config.json`, `progress.json` |
| `world_hooks` | `world_hooks.md` |
| `voice_config` | `voice_config.json` |
| `volume_arc` | `volume_arc.md` |
| `plan_volume_events` | `planning/volume_{n}/volume_event_plan.json` + `plot_workshop_volume_{n}.json` |
| `plan_event` | `events/event_{id}_outline.md` + `plot_workshop_event_{id}.json` |
| `plot_workshop` | `plot_workshop_volume_{n}.json` / `plot_workshop_event_{id}.json` / 章级 JSON |
| `plot_engine` | `plot_engine_volume_{n}.md` / `plot_engine_event_{id}.md` / 章级 MD |
| `chapter_beats` | `plot_engine/chapter_beats_{start}-{end}.md` |
| `plot_workshop` | `plot_workshop.json` 或 `plot_workshop_chapter_{n}.json` |
| `plot_engine` | `plot_engine.md` 或 `plot_engine_chapter_{n}.md` |

### 自动回灌字段

`ConfigManager.get_context_snapshot()` 会自动补齐：

- `plot_workshop`
- `plot_engine`
- `trope_hint`
- `progress_node`
- `relationship_context`
- `faction_context`
- `voice_config`
- `chapter_workflow`

`PhaseRunner.prepare_chapter()` 会在未显式传参时自动回填：

- `workshop_result`
- `trope_hint`
- `plot_engine_result`
- `relationship_context`
- `faction_context`

### ⚠️ workflow_state.json 维护陷阱

**问题**：用 `patch` 工具直接修改 `workflow_state.json` 的 notes 字段时，会导致 JSON 损坏：
1. 中文引号（'）、长箭头（→）等字符的双转义（`\"` → `\\\"` → `\\\\\\\"`）
2. 实际换行符（0x0a）嵌入 JSON 字符串值内部
3. JSON 文件整体损坏，`json.load()` 抛出 `JSONDecodeError`

**禁止做法**：❌ 用 `patch` 工具修改 `workflow_state.json` 的 notes 字段

**正确做法**：用 Python 完整重建 JSON
```python
import json
with open('config/workflow_state.json') as f:
    data = json.load(f)
data['chapter_021'] = {
    "outline": "completed",
    "draft": "completed",
    "final": "completed",
    "notes": "使用普通引号避免转义问题..."
}
with open('config/workflow_state.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

**恢复方法**：若已损坏，用 `json.dump()` 重建整个文件。不要逐字符修复——直接重建最可靠。

### 字数不足时的扩充策略

**问题**：草稿创建后汉字字数不达标（<1800），反复微调浪费大量时间。

**有效策略**（按优先级）：
1. ⭐⭐ 扩充对话——在现有场景中自然延长对话交换（每轮+50-80字）
2. ⭐⭐ 增加角色反应细节——微表情、身体动作、环境感知（+20-40字/处）
3. ⭐ 增加场景感官描写——温度、光线、气味、声音（+15-30字/处）
4. ⭐ 增加配角视角过渡——但不展开为独立场景

**无效做法**：❌ 先写短→再逐句加字→反复检查字数。应该一次性写出足够篇幅。

**经验值**：对话章容易达标（30%+），独白/内心戏章天然偏低（5-15%），过渡/卷末章允许1700-1800字。

### 扩充策略优先级（完整版）

当字数不足时，按以下优先级执行扩充：

| 优先级 | 策略 | 每处字数增益 | 适用场景 |
|:------:|:-----|:-----------:|:---------|
| ⭐⭐ | 扩充对话 | +50-80字/轮 | 对话比<20%，场景有角色在场 |
| ⭐⭐ | 角色反应细节 | +20-40字/处 | 情绪过渡突兀，缺身体反应 |
| ⭐ | 场景感官描写 | +15-30字/处 | 场景泛泛，缺温度/光线/声音/气味 |
| ⭐ | 配角视角过渡 | +15-25字/处 | 单一视角过长，需要切换节奏 |

**禁止做法**：❌ 小幅度累加修补——通过+5+10字的小改动反复patch累计30+次来凑字数。每次修改都可能引入新的违规，且文本连贯性不断下降。应在初稿阶段至少达到60-70%目标字数再进入质量检查。

### 批量章节扩充——子代理工作流

当3+章同时需要扩充（如卷末章节批量偏短）时：

1. 扫描所有章节汉字数，识别偏短的章节（<1800字）
2. 按章节分组，每3章为一个批处理单元
3. 扩充指令必须包含：章节核心剧情、角色人设约束、禁止句式（`不是X是Y`）
4. 每批完成后验证：汉字数、管理词、`不是X是Y`句式
5. 最终统一更新 project 配置文件

**关键约束**：子代理无跨章记忆，每章上下文必须完整自包含。

### 批量章节创作节奏

当用户**明确要求**连续创作多章（5+）且授权加快节奏时：

1. 一次性读取所有需要的上下文（节拍表、角色卡、最新终稿）
2. 每章生成 `plot_workshop` + `plot_engine` 后，调用 `write_chapter(stage="draft", batch_mode=True)`  
   - `batch_mode=True` 会自动确认已生成大纲，或用 plot_engine 合成最小大纲  
   - **禁止**在未获用户授权时擅自使用 batch_mode
3. 质量检查在每章完成后立即执行
4. 登录文件在最后统一更新

## 前置检查：前章溢出覆盖处理（5步法）

当上一章终稿实际内容覆盖了当前章的**全部或大部分**规划节拍时触发。

### 触发检测

每次写大纲前必须做：读取上一章终稿 → 对比当前章plot_engine的节拍表 → 逐条标记"已覆盖/未覆盖"

### 5步法

1. **逐Beat对比** — 将当前章每个beat与上一章终稿逐条对照
2. **判断覆盖度** — 全部覆盖→重设计为桥接章；部分覆盖→保留未覆盖beat，替换已覆盖beat
3. **桥接章设计模板**（适用于大时间跨度）：
   - 承接（~10%）：从上一章结尾自然过渡
   - 时间跳跃压缩（~40%）：用灵气变化/修为进度/环境变迁标记时间流逝
   - 世界观铺垫（~15%）：主角以观察者视角记录变化（不介入）
   - 关系维系（~10%）：通过远程连接（逆鳞/共生感知）维持与已离场角色联系
   - 衔接钩子（~25%）：抵达下一章起点，感知到关键气息/事件前兆
4. **约束检查**：❌不引入新角色深入互动、❌不重复已完成内容、✅必须与后续章节无缝衔接
5. **落盘新产物** — 生成新的 `plot_workshop_chapter_{n}.json` 和 `plot_engine_chapter_{n}.md`

## 前置检查：配置文件强制清单（4文件缺一不可）

每次开始创作前，必须一次性读取以下5个文件：

| 文件 | 关键字段 | 漏检后果 |
|------|---------|---------|
| `config/workflow_state.json` | 当前章节+状态 | 章节进度错位 |
| `config/character_cards.json` | 角色位置/修为/物品/关系 | 物品重复赠送、关系状态错误 |
| `config/novel_writer_config.json` | 项目配置 | 当前任务/位置/状态错误 |
| `config/voice_config.json` | 人味计划/反AI味/管理词/输出格式 | 隐藏人味缺失、反AI味失效、管理词入正文 |
| `plot_engine/plot_workshop_chapter_{n}.json` + `plot_engine/plot_engine_chapter_{n}.md` | 本章桥段与推演 | 大纲/正文缺上游输入 |

**⚠️ 严格执行警告**：禁止简化流程、跳过文件或分批次读取。用户会立即发现并纠正流程违规，违规后必须重新开始，补全漏读文件。

## 章节流程约束 / Chapter Workflow

```text
write_chapter(stage="outline")
-> confirm_step(step="outline")
-> write_chapter(stage="draft")
-> confirm_step(step="draft")
-> finalize_chapter
```

约束规则：

- `workflow_state.json` 记录每章大纲、草稿、终稿状态
- 未确认大纲时禁止生成正文
- 未确认草稿时禁止终稿入库
- 大纲 Prompt 必须对照节拍表、工坊结果、剧情推演结果
- 草稿 Prompt 必须承接已确认大纲，同时吸收关系摘要、阵营摘要、工坊骨架、剧情推演结果
- 正文默认只输出标题和正文，不输出执行说明
- 正文禁止出现 `章/卷/篇/上章/下章/本章/下一章/上一章` 等管理词

### ⚠️ workflow_state.json 维护陷阱

**问题**：`patch` 工具在替换含有中文引号（'）、长箭头（→）、特殊字符的 notes 字段时，会导致：
1. 双引号被双重转义（`\"` → `\\\"`）
2. 实际换行符（0x0a）嵌入 JSON 字符串值内部
3. JSON 文件整体损坏，无法解析

**禁止做法**：❌ 用 `patch` 工具直接修改 `workflow_state.json` 的 notes 字段

**正确做法**：
```python
import json
# 用 Python 完整重建 JSON 文件
with open('config/workflow_state.json') as f:
    data = json.load(f)

# 修改数据
data['chapter_021'] = {
    "outline": "completed",
    "draft": "completed",
    "final": "completed",
    # ... 注意：notes 字段中可以使用 '...' 中文引号
    "notes": "终稿：约2315汉字。核心剧情：林雪被上司约谈..."
}

# 写回文件（关键参数）
with open('config/workflow_state.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

**恢复方法**：若 workflow_state.json 已损坏，用 Python 的 `json.dump()` 重建整个文件。不要尝试逐字符修复——直接重建最可靠。

## 上游产物缺失恢复 / Upstream Artifact Recovery

当项目已存在、当前章节处于 `outline_pending` 状态时，必须先检查上游产物是否存在。若缺失，不得直接进入 `write_chapter`，必须先补全上游产物。

### 检查清单

对应第 N 章，检查以下文件是否存在：
- `plot_engine/plot_workshop_chapter_{N}.json`
- `plot_engine/plot_engine_chapter_{N}.md`
- `plot_engine/chapter_beats_*.md` 中第 N 章节拍（可能仅有"原始规划"）

### 补全流程（严禁跳过）

1. **读取前序章节状态**
   - 读取第 N-1 章的 `plot_workshop`、`plot_engine`、`outline`、`draft`
   - 确定下班接点和角色当前状态

2. **读取当前角色卡**
   - 读取 `config/character_cards.json`，确认各角色位置、修为、关系、物品
   - 读取 `config/voice_config.json` 确保风格约束一致

3. **读取节拍表**
   - 从 `chapter_beats_*.md` 中提取第 N 章节拍（即使是原始规划也要读）

4. **生成 `plot_workshop_chapter_{N}.json`**
   - 基于前序状态 + 角色卡 + 节拍表原始规划，手动构建桥段骨架
   - 必须包含：selected_trope、plot_outline、scene_beats、constraints、context_summary
   - 产物落盘至 `plot_engine/plot_workshop_chapter_{N}.json`

5. **生成 `plot_engine_chapter_{N}.md`**
   - 基于 plot_workshop 结果 + 角色当前状态，撰写剧情推演
   - 必须包含：承接点、剧情推演、人味锚点
   - 产物落盘至 `plot_engine/plot_engine_chapter_{N}.md`

6. **验证**
   - 确认两个文件已成功写入磁盘
   - 确认与前序章节节奏连贯
   - 确认角色状态与 character_cards 一致

7. **确认**
   - 将补全结果汇报用户，获得显式确认后，才能进入 `write_chapter(stage="outline")`

## 剧情工坊 / Plot Workshop

v3.0 主链在**卷级/事件级**编排；章级 `plot_workshop` **默认关闭**。

`plot_workshop` scope：

- `scope=volume`：卷内事件卡片（规则默认；`use_llm=True` 可选精炼）→ `plot_workshop_volume_{n}.json`
- `scope=event`：单事件 scene_beats / constraints → `plot_workshop_event_{id}.json`
- `scope=chapter`：保留 per-chapter，**仅** `plot_workshop_per_chapter_enabled=true` 时启用

- `selected_trope`
- `plot_outline`
- `scene_beats`
- `constraints`
- `context_summary`

其作用不是直接写正文，而是提供：

- 冲突骨架
- 场景组织建议
- 情绪与回报方向
- 后续 `plot_engine` 的输入基础

## 剧情推演 / Plot Engine

v3.0 主链不依赖章级推演。章级 `plot_engine` **默认关闭**。

`plot_engine` scope：

- `scope=volume` → `volume_event_plan.json` + `plot_engine_volume_{n}.md`
- `scope=event` → `event_{id}_outline.md` + `plot_engine_event_{id}.md`
- `scope=chapter` → 保留现有，需 `plot_engine_per_chapter_enabled=true`

章级推演会吸收：

- 世界观爽点
- 当前节拍节点
- 角色当前状态
- 工坊桥段提示
- 工坊桥段包

其产出会自动回灌到：

- 章节大纲生成
- 草稿生成
- 隐藏人味计划中的"剧情推演摘要"

## 草稿阶段增强 / Draft Enhancements

草稿阶段额外能力：

- 自动构建"隐藏人味计划"
- 自动注入角色关系摘要与阵营压力
- 自动做人味校验
- 命中风险时自动触发一次最小必要二次修整

重点检查项：

- 抽象情绪词过量
- 解释句过量
- 陈词滥调
- 未解析占位符
- 正文管理词污染

### 写作检查三问

写完一段后问自己（优先级从高到低）：

1. **这段是角色在做事，还是我在描述角色？**
   — 主角应该主动做决策、遇到阻碍、做选择，不应该被描述成被动接收器
2. **这段有情绪流动吗？**
   — 紧张→释放→新的紧张，情绪应该有曲线，不是静态标签
3. **这段删掉后，剧情/人物/情绪有损失吗？**
   — 如果都没有，删掉。没有不可替代作用的段落就是冗余。

### 约束过载陷阱

**症状**：过多的"禁止/不得/必须检查"的负面约束导致避错导向的写作，写出来的东西安全但没有生命。人物像无情的机器，每章结构雷同。

**根因**：7条禁止+9条清单+指标要求形成"不犯错"导向。写作出发点从"角色会怎么做"变成了"这条规则能不能破"。

**修正原则**：
1. **正面引导代替负面清单** — 用"建议这样写"代替"不能写X"
2. **指标弹性化** — 字数/对话比/省略号是指南不是镣铐，先写完整章节再微调
3. **人物意志驱动** — 问"主角想要什么→遇到什么阻碍→做了什么选择"，不问"违不违反规则"

## 穿越者视角规范

穿越者（熟知世界原剧情）的写作必须遵守以下原则：

### 核心原则

| 场景 | ❌ 错误（非穿越者写法） | ✅ 正确（穿越者写法） |
|------|----------------------|---------------------|
| 重要角色登场 | "在心里记住了名字" | "和记忆中的对上了——该来的都来了" |
| 知名事件发生 | "这人怎么哭哭啼啼的" | "准提哭座——原剧情里确实有这一出" |
| 格局确认 | "把六个人的名字过了一遍" | "全对上了。六个圣位的格局和穿越前完全一致" |

### 三条黄金规则

1. **已知事件不惊讶** — 穿越者不会对知名的洪荒大事件感到新奇
2. **做验证而非发现** — 应该是"和记忆里对上了"而非"原来是这样"
3. **未知设定=探索机会** — 遇到穿越前不知道的设定，反应是"探索/惊喜/抓住机会"

## 对话占比弹性标准

对话占比目标应因章节类型灵活调整，质量优先于指标：

| 章节类型 | 可接受范围 | 说明 |
|----------|:----------:|------|
| 正常叙事章 | 20-40% | 标准范围 |
| 过渡/时间跳跃章 | 15-20% | 对话机会自然少 |
| 观察/筛选章 | 12-18% | 主角以观察为主 |
| 战斗章 | 15-30% | 战斗描写占主体 |
| 重逢/内心觉醒章 | 28-32% | 需内心描写展现认知转变 |
| 对话推进章 | 45-60% | 几乎全章靠对话推进 |

**禁止**：为凑对话占比而添加冗余交流。每句对话必须是信息传递，非情感确认。

## 角色卡管理约束

### 1. 身份保密规则（剧情引擎时序优先）

即使 narrative 中给了暗示，只要**主角尚未正式知晓**，角色卡中必须保持保密：

| 剧情状态 | 角色卡处理 |
|---------|-----------|
| 引擎设定第55章揭晓 | 第52章角色卡仍写"身份不明" |
| 给了暗示但主角未确认 | 不记录暗示信息 |
| 主角正式知晓 | 立即更新角色卡 |

### 2. 关系温差追踪

关系温差 = 表面态度 vs 真实态度的差异，是角色卡必须记录的数据：

| 维度 | 示例 |
|------|------|
| 表面态度 | 敖灵：嘴上嫌弃、债务锚点 |
| 真实态度 | 敖灵：关心、不舍 |
| 温差表现 | 耳根微红、别过脸去、塞给鳞片 |
| 变化趋势 | 从"强烈温差"到"温差缩小"

## 角色关系系统 / Relationship System

- 支持 22 种关系类型
- 关系指标包括 `intimacy`、`trust`、`conflict`
- 支持 `reverse_type`，可表达 `parent/child`、`master/apprentice`、`subordinate/superior` 等非对称关系
- 支持关系一致性检查、阵营冲突检测、剧情推荐

## 作者签名 / Author Profile

- 配置文件：`config/author_profile.json`（`init` 时从 `references/author_profile.template.json` 复制）
- **per-author**：`author_signature`（tone、humor、mature_content、daily_life_texture）跨项目复用
- **per-project**：`genre`、`core_pleasure` 在 `novel_writer_config.json` 或 action 参数中指定
- `voice_config` 生成后**强制合并** `author_signature`；题材不得覆盖签名
- `core_pleasure` / `genre` 默认均为「未指定」，禁止写死「升级」「玄幻」

## 参考 Prompt（未接线 action）

| 文件 | 状态 |
|------|------|
| `prompts/protagonist_engine.md` | 参考用，无主链 action |
| `prompts/relationship_analyze.md` | 参考用；关系逻辑见 `relationship_manager` actions |

已移除：`prompts/writing_style.md`（并入 `voice_config.md`）、`templates/chapter_write_v142.md`

## 架构 / Architecture

```text
novel-writer/
├── prompts/
│   ├── world_hooks.md
│   ├── voice_config.md
│   ├── volume_arc.md
│   ├── chapter_beats.md
│   ├── plot_engine.md
│   ├── chapter_hook.md
│   └── chapter_write.md
├── references/
│   └── author_profile.template.json
├── scripts/
│   ├── openclaw_entry.py
│   ├── config_manager.py
│   ├── phase_runner.py
│   ├── writing_loop.py
│   ├── plot_workshop.py
│   ├── relationship_manager.py
│   ├── relationship_validator.py
│   ├── plot_recommender.py
│   ├── style_validator.py
│   └── plot_engine.py
├── relationship_types.json
└── fusion-writer-template.json
```

说明：

- `plot_engine.py` 仍是占位辅助文件
- 实际剧情推演主逻辑由 `prompts/plot_engine.md` + `scripts/openclaw_entry.py` 驱动
- `plot_workshop.py` 负责桥段骨架生成
- `phase_runner.py` 负责把上游产物拼装进 outline / draft Prompt
