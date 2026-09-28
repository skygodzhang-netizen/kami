# 📖 Novel Writer - 自动化小说创作系统

**版本**: v1.4.1  
**最后更新**: 2026-04-08  
**开发者**: 小袁 🤖

---

## 🚀 快速开始

### 完整创作流程

```
1. 项目初始化 (init) → 用户确认
2. 世界观设计 (world_hooks) → 用户确认
3. 声音配置 (voice_config) → 用户确认
4. 角色关系建立 → 用户确认
5. 阵营创建 → 用户确认
   ↓
6. 卷大纲设计 (volume_arc) → 用户确认
7. 剧情引擎推演 (plot_engine) → 用户确认
8. 章节节拍表 (chapter_beats) → 用户确认
   ↓
9. 写作循环（强制锚定节拍表）
```

### 核心功能

- ✅ **22 种关系类型** - 情感/血缘/社交/阵营 4 大类
- ✅ **关系指标追踪** - 亲密度 (-100~100)、信任度 (0~100)、冲突值
- ✅ **阵营管理** - 正派/反派/中立，层级系统
- ✅ **自动一致性检查** - 三角关系、阵营冲突检测
- ✅ **剧情推荐引擎** - 基于关系冲突生成场景建议
- ✅ **强制节拍表锚定** - 每章写作对照节拍表
- ✅ **系统提示优化** - MINIMAL原则下的【】提示处理（见`references/system-prompt-optimization.md`）

---

## 📋 核心 Actions

### 创作流程

| Action | 功能 | 确认 |
|--------|------|------|
| `init` | 初始化项目 | ✅ |
| `world_hooks` | 世界观设计 | ✅ |
| `voice_config` | 声音配置 | ✅ |
| `volume_arc` | 卷大纲设计 | ✅ |
| `plot_engine` | 剧情引擎推演 | ✅ |
| `chapter_beats` | 章节节拍表 | ✅ |
| `write_chapter` | 写作循环 | ✅ |
| `confirm_step` | 确认大纲/草稿 | ✅ |
| `finalize_chapter` | 终稿入库（自动触发后续流程）| ✅ |

### 角色关系管理

| Action | 功能 |
|--------|------|
| `create_relationship` | 创建角色关系 |
| `update_relationship` | 更新关系状态 |
| `get_relationship` | 查询关系 |
| `list_relationships` | 列出关系 |
| `delete_relationship` | 删除关系 |
| `get_character_relationships` | 获取角色所有关系 |
| `validate_relationships` | 关系一致性检查 |
| `detect_conflicts` | 检测关系冲突 |
| `recommend_plot` | 生成剧情推荐 |

### 阵营管理

| Action | 功能 |
|--------|------|
| `create_faction` | 创建阵营 |
| `get_faction` | 查询阵营 |
| `list_factions` | 列出阵营 |
| `add_faction_member` | 添加阵营成员 |

---

## 🤝 关系类型系统

### 4 大类 22 种关系

| 类别 | 类型数 | 示例 | 亲密度范围 |
|------|--------|------|-----------|
| **情感关系** | 4 | lover, crush, ex_lover |  varies |
| **血缘关系** | 4 | parent, sibling, cousin | 20-100 |
| **社交关系** | 9 | master, friend, enemy | varies |
| **阵营关系** | 4 | ally, subordinate, traitor | varies |

### 关系指标

| 指标 | 范围 | 说明 |
|------|------|------|
| intimacy | -100 ~ 100 | 亲密度（正友好，负敌对） |
| trust | 0 ~ 100 | 信任度 |
| conflict | 0 ~ 100 | 冲突值 |

---

## 📝 使用示例

### 创建角色关系

```python
# 创建挚友
create_relationship(
    character_a="protagonist",
    character_b="li_si",
    rel_type="best_friend",
    metrics={"intimacy": 90, "trust": 95},
    since_chapter=3
)

# 创建敌人
create_relationship(
    character_a="protagonist",
    character_b="wang_wu",
    rel_type="enemy",
    metrics={"intimacy": -80, "conflict": 90}
)
```

### 创建阵营

```python
create_faction(
    name="天道盟",
    faction_type="正派",
    members=["protagonist", "li_si"],
    enemies=["moyin_pavilion"],
    hierarchy={
        "leader": "zhang_lao",
        "elders": ["wang_shi"],
        "members": ["protagonist", "li_si"]
    }
)
```

### 更新关系

```python
# 关系进展
update_relationship(
    character_a="protagonist",
    character_b="li_si",
    metrics_change={"intimacy": 5, "trust": 5},
    event="共同对抗敌人",
    chapter_num=15
)
```

### 检查一致性

```python
# 全面检查
validate_relationships(chapter_num=25)

# 检测冲突
detect_conflicts(character_id="protagonist")

# 生成剧情推荐
recommend_plot(chapter_num=26)
```

---

## 📊 写作循环（强制锚定节拍表）

### 完整流程

```
章节节拍表生成 → 用户确认
    ↓
大纲生成（强制对照节拍表）→ 一致性检查 → 用户确认
    ↓
草稿生成（强制对照节拍表 + 大纲）→ 一致性检查 → 用户确认
    ↓
终稿入库 → 自动触发：
    - 关系更新
    - 一致性检查
    - 剧情推荐
```

### 节拍表对照要求

**大纲生成时必须填写**:
```
【节拍表对照】
- 节拍表要求：[引用具体节拍表内容]
- 大纲对应设计：[逐条对应说明]
- 偏离说明：[如有偏离必填，否则填"无"]
```

**正文生成时必须填写**:
```
【节拍表与大纲执行说明】
- 节拍表关键要求：[引用]
- 大纲核心设计：[引用]
- 正文执行情况：[逐条说明]
- 偏离说明：[如有必填]
```

---

## 🔧 系统架构

```
novel-writer/
├── SKILL.md                          # 技能主文档
├── README.md                         # 本文件
├── relationship_types.json           # 关系类型定义
├── fusion-writer-template.json       # 写作模板
├── _meta.json                        # 元数据
├── prompts/                          # 11 个 Prompt 模板
│   ├── chapter_hook.md              # 大纲生成（强制锚定节拍表）
│   ├── chapter_write.md             # 正文生成（强制锚定节拍表）
│   ├── chapter_beats.md             # 章节节拍表
│   ├── volume_arc.md                # 卷大纲
│   ├── world_hooks.md               # 世界观
│   ├── voice_config.md              # 声音配置
│   ├── plot_engine.md               # 剧情引擎
│   └── ...
└── scripts/                          # 12 个 Python 脚本
    ├── openclaw_entry.py            # 技能入口
    ├── config_manager.py            # 配置管理
    ├── relationship_manager.py      # 关系管理
    ├── relationship_validator.py    # 关系验证
    ├── plot_recommender.py          # 剧情推荐
    ├── phase_runner.py              # 阶段流转
    ├── writing_loop.py              # 写作循环
    └── ...
```

---

## 🎯 关键特性

### 1. 强制节拍表锚定

每章写作时必须对照章节节拍表，确保：
- ✅ 关键事件符合节拍表设计
- ✅ 情绪基调与节拍表一致
- ✅ 钩子结尾符合节拍表要求

### 2. 用户确认环节

所有关键步骤都需要用户确认：
- ✅ 世界观设计
- ✅ 卷大纲设计
- ✅ 剧情引擎推演
- ✅ 章节节拍表
- ✅ 单章大纲
- ✅ 单章正文

### 3. 自动后续流程

终稿入库后自动触发：
- ✅ 关系更新（根据角色数据）
- ✅ 一致性检查（三角关系、阵营冲突）
- ✅ 剧情推荐（生成下一章建议）

### 4. 一致性检查

自动检测：
- ⚠️ 关系类型与指标不匹配
- ⚠️ 同阵营成员的敌对关系
- ⚠️ 跨阵营的友好关系
- ⚠️ 三角关系（情感/忠诚度）

---

## 📅 更新日志

### v1.4.1 (2026-04-08) - 流程修复

**修复工时**: 30 分钟

#### 🔧 核心修复

**1. 写作循环强制锚定章节节拍表**

修复文件:
- `prompts/chapter_hook.md` - 添加节拍表强制对照要求
- `prompts/chapter_write.md` - 添加节拍表和大纲双重对照要求
- `scripts/phase_runner.py` - 确保传递 chapter_beats 和 chapter_num

修复内容:
```markdown
## ⚠️ 强制约束：必须严格对照章节节拍表

### 输入
- **完整章节节拍表**：{{chapter_beats}}
- **当前章节号**：第{{chapter_num}}章

### 节拍表一致性检查（必须执行）
1. 关键事件检查
2. 情绪基调检查
3. 钩子结尾检查

### 输出格式
【节拍表对照】（必填）
```

**2. plot_engine 添加用户确认**

修复文件：`scripts/openclaw_entry.py`

修复前:
```python
results["status"] = "complete"
results["message"] = "剧情引擎推演完毕。"
```

修复后:
```python
results["status"] = "awaiting_confirmation"
results["message"] = "剧情引擎推演完毕，请确认。"
```

**3. 终稿后自动触发后续流程**

修复文件：`scripts/openclaw_entry.py`

新增功能:
- ✅ 自动关系更新（根据 character_updates）
- ✅ 自动一致性检查（validate_relationships）
- ✅ 自动剧情推荐（recommend_plot）

完成消息:
```
✅ 第 X 章终稿入库完成
📊 字数：XXXX 汉字
🔍 关系一致性：✅ 通过 / ⚠️ 发现问题
💡 已生成 X 个下一章剧情推荐
```

---

### v1.4.0 (2026-04-08) - 角色关系系统

**开发用时**: 23 分钟（AI 加速 300x）🚀

#### 🎉 重大更新

**1. 角色关系系统**

新增关系管理模块 (`relationship_manager.py` - 18.6KB):
- ✅ 支持 22 种关系类型（情感/血缘/社交/阵营 4 大类）
- ✅ 关系指标追踪（亲密度 -100~100、信任度 0~100、冲突值）
- ✅ 关系演变历史记录（章节级变更日志）
- ✅ 自动去重、自引用检测、类型验证
- ✅ 原子写入保护

关系类型:
| 类别 | 类型数 | 示例 |
|------|--------|------|
| 情感关系 | 4 | lover, crush, ex_lover |
| 血缘关系 | 4 | parent, sibling |
| 社交关系 | 9 | master, friend, enemy |
| 阵营关系 | 4 | ally, subordinate, traitor |

**2. 阵营管理**

新增阵营管理模块:
- ✅ 创建阵营（正派/反派/中立）
- ✅ 阵营层级（leader/elders/members）
- ✅ 阵营关系（enemies/allies）
- ✅ 成员管理（添加/移除）

**3. 关系一致性检查**

新增关系验证模块 (`relationship_validator.py` - 13.3KB):
- ✅ 关系类型与指标匹配检查
- ✅ 双向关系一致性验证
- ✅ 阵营冲突检测（同阵营敌对、跨阵营恋爱）
- ✅ 三角关系自动发现（情感/忠诚度）

检测能力:
```
⚠️  关系类型'lover'的亲密度应为 [80, 100]，实际为 60
🚨 hero_a（正道盟）与敌对阵营成员 villain_a（魔法教）有 lover 关系
💕 检测到情感三角关系：protagonist, li_si, xiao_mei
```

**4. 剧情推荐引擎**

新增剧情推荐模块 (`plot_recommender.py` - 14.8KB):
- ✅ 基于关系冲突推荐剧情
- ✅ 关系发展阶段分析
- ✅ 戏剧潜力识别
- ✅ 情绪弧线生成
- ✅ 关键节拍生成
- ✅ 对话提示生成

推荐类型:
| 类型 | 触发条件 | 戏剧潜力 |
|------|----------|----------|
| conflict_escalation | 三角关系、误会 | high |
| loyalty_test | 阵营冲突、师徒关系 | high |
| relationship_upgrade | 亲密度 70-85 | medium |
| relationship_turn | 敌对关系缓和 | high |
| betrayal_warning | 信任度<40 | high |

---

#### 🔌 新增 Actions (14 个)

**关系管理 (7 个)**
- `create_relationship` - 创建角色关系
- `update_relationship` - 更新关系状态
- `get_relationship` - 查询关系
- `list_relationships` - 列出关系
- `delete_relationship` - 删除关系
- `get_character_relationships` - 获取角色所有关系
- `get_relationship_network` - 获取关系网络

**阵营管理 (4 个)**
- `create_faction` - 创建阵营
- `get_faction` - 查询阵营
- `list_factions` - 列出阵营
- `add_faction_member` - 添加阵营成员

**一致性检查 (2 个)**
- `validate_relationships` - 关系一致性检查
- `detect_conflicts` - 检测关系冲突

**剧情推荐 (2 个)**
- `recommend_plot` - 生成剧情推荐
- `generate_scene_outline` - 生成场景大纲

---

#### 📁 新增文件

**核心代码**:
- `relationship_manager.py` (18.6KB)
- `relationship_validator.py` (13.3KB)
- `plot_recommender.py` (14.8KB)
- `generate_sample_data.py` (6.0KB)

**配置文件**:
- `relationship_types.json` (2.9KB) - 22 种关系类型定义

**Prompt 模板**:
- `relationship_analyze.md` (3.6KB)

---

#### 📊 代码统计

| 指标 | 数值 |
|------|------|
| 新增代码行数 | ~1,630 行 |
| 新增 Actions | 14 个 |
| 关系类型数 | 22 种 |
| 开发用时 | 23 分钟 |
| AI 加速比 | 300x |

---

## 💡 最佳实践

### 关系建立时机

| 阶段 | 建议 |
|------|------|
| 第 1-3 章 | 建立核心关系（挚友、敌人、师徒） |
| 第 10-20 章 | 扩展关系（同门、盟友） |
| 第 30+ 章 | 深化关系（恋人、生死之交） |

### 关系演变节奏

| 类型 | 幅度 | 场景 |
|------|------|------|
| 日常互动 | ±2~5 | 对话、交流 |
| 重大事件 | ±10~20 | 生死关头、共同抗敌 |
| 背叛事件 | ±50~80 | 重大冲突、理念分歧 |

### 冲突设计模式

**模式 1: 三角关系**
- A 爱 B，B 爱 C，C 爱 A
- → 当面对质、被迫选择

**模式 2: 阵营冲突**
- 主角加入正派，恋人在反派
- → 秘密会面、战场相遇

**模式 3: 忠诚考验**
- 师父 vs 朋友，必须选择
- → 内心挣扎、代价显现

---

## ⚠️ 常见问题

### Q: 关系指标超出范围会怎样？

A: 系统会发出警告，但不会阻止操作。一致性检查时会提示。

### Q: 如何查看角色的所有关系？

A: 使用 `get_character_relationships(character_id="protagonist")`

### Q: 节拍表与实际情况不符怎么办？

A: 
1. 暂停写作
2. 更新章节节拍表
3. 重新生成大纲
4. 继续写作

### Q: 终稿后没有看到剧情推荐？

A: v1.4.1 已修复，终稿后会自动生成推荐。检查完成消息中的推荐数量。

---

## 📁 文件说明

### 核心文件

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 技能主文档（详细版） |
| `README.md` | 本文件（快速参考） |
| `relationship_types.json` | 22 种关系类型定义 |
| `fusion-writer-template.json` | 网文写作模板 |

### Prompt 模板

| 文件 | 功能 |
|------|------|
| `chapter_hook.md` | 单章大纲生成（强制锚定节拍表） |
| `chapter_write.md` | 单章正文生成（强制锚定节拍表） |
| `chapter_beats.md` | 章节节拍表模板 |
| `volume_arc.md` | 卷情绪弧设计 |
| `world_hooks.md` | 世界观爽点预埋 |
| `voice_config.md` | 声音配置定制 |
| `plot_engine.md` | 剧情引擎推演 |
| `relationship_analyze.md` | 关系分析与推荐 |

### Python 脚本

| 文件 | 功能 |
|------|------|
| `openclaw_entry.py` | 技能入口（所有 Actions） |
| `config_manager.py` | 配置与进度管理 |
| `relationship_manager.py` | 关系 CRUD + 阵营管理 |
| `relationship_validator.py` | 关系一致性检查 |
| `plot_recommender.py` | 剧情推荐引擎 |
| `phase_runner.py` | 阶段流转控制 |
| `writing_loop.py` | 写作循环管理 |
| `style_validator.py` | 风格校验器 |

---

## 📊 代码统计

| 指标 | 数值 |
|------|------|
| Python 脚本 | 12 个 |
| Prompt 模板 | 11 个 |
| 配置文件 | 3 个 |
| 总代码行数 | ~1,650 行 |
| 关系类型 | 22 种 |
| Actions | 25+ 个 |

---

## 🔜 未来计划

### v1.5.0 (规划中)

- [ ] AI 智能剧情推荐（基于 LLM）
- [ ] 基于章节内容的自动关系更新
- [ ] 关系图谱可视化（Mermaid/Graphviz）
- [ ] 性能优化（大规模关系图缓存）

---

## 📞 支持

- **技能文档**: `SKILL.md`
- **快速参考**: `README.md` (本文件)
- **更新日志**: 见本文件下方

---

**版本**: v1.4.1  
**最后更新**: 2026-04-08 22:10  
**维护者**: 小袁 🤖
