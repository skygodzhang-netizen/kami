# 任务：定制专属声音配置（Voice Config）

基于《基础写作风格模板》和《小说世界观大纲》，为当前小说生成一份专属的声音配置。

## 输入信息
- **题材（per-project）**：{{genre}}
- **作者签名（per-author，不可被题材覆盖）**：{{author_signature}}
- **擦边内容政策**：{{mature_content_policy}}
- **完整作者配置**：{{author_profile}}
- **世界氛围**：{{world_atmosphere}}（热血/暗黑/轻松/紧张等）
- **主角性格**：{{protagonist_personality}}（坚韧/狡猾/冷静/热血等）
- **目标平台**：{{target_platform}}（番茄/起点/七猫/飞卢）
- **世界观**：{{world_hooks}}

> **优先级**：`author_signature`（日常/搞笑/擦边边界）**优先于**题材默认的「爽文语气」。题材只调整 pacing、worldbuilding 等结构字段，**不得**改写 `author_signature` 与 `mature_content_policy`（落盘时由系统从 `author_profile.json` 强制合并）。

### 步骤0：作者签名（author_signature）— 强制透传

从 `author_profile` 读取并**原样写入**输出 JSON 的以下字段（可微调 `humor.notes` 措辞，但不可关闭 humor/mature 开关）：

```json
{
  "author_signature": {
    "tone": ["日常", "搞笑"],
    "humor": {
      "enabled": true,
      "style": "冷幽默、吐槽、反差",
      "density": "medium"
    },
    "mature_content": {
      "enabled": true,
      "level": "mild",
      "boundaries": ["可暧昧擦边暗示，不写露骨细节"],
      "avoid": ["未成年人", "强迫情节"]
    },
    "daily_life_texture": true
  },
  "mature_content_policy": {
    "platform_safe": true,
    "reminder_only": true,
    "summary": "擦边以暗示留白为主"
  }
}
```

**mature_content_policy 生成说明**：
- `level=mild`：暧昧、双关、留白，禁止直白描写
- `level=off`：完全不写擦边（仅当 author_profile 如此配置）
- 政策字段供 StyleValidator **提醒**用，不用于阻断创作

## 处理流程

### 步骤1：继承基础模板
基于以下网文实战配置模板，根据输入信息进行定制化：

```json
{
  "_meta": {
    "version": "4.0-webnovel",
    "description": "网文实战配置 - 情绪驱动、节奏抓人、人味优先",
    "target_platforms": ["{{target_platform}}"],
    "core_philosophy": "爽感>信息>文笔，情绪>逻辑>精致"
  },
  "narrative": {
    "voice": "第三人称限知（主角视角）",
    "primary_driver": "情绪推进",
    "secondary_driver": "冲突升级",
    "writing_mode": "展示+讲述混合，该快则快该慢则慢"
  },
  "pacing": {
    "rhythm_principles": {
      "default": "快节奏推进，慢节奏只用于关键情绪点"
    },
    "scene_structure": {
      "opening": {
        "goal": "3句话内进入剧情或抓住注意力"
      },
      "development": {
        "density": "章节整体持续推进，避免机械打点"
      }
    }
  },
  "dialogue": {
    "density": "medium-high",
    "target_ratio": "30-50%"
  },
  "quality_thresholds": {
    "chapter_length": {
      "min": 2000,
      "ideal": "2500-3500",
      "max": 5000
    }
  }
}
```

### 步骤2：世界观定制化
根据题材类型 `{{genre}}` 和世界氛围 `{{world_atmosphere}}` 修改以下字段：

| 题材类型 | 修改重点 |
|----------|----------|
| 仙侠/玄幻 | pacing.scene_types.沉淀.paragraph_max降至60，增加打斗动作描写比重；worldbuilding增加"修炼体系可视化" |
| 悬疑/推理 | pacing.scene_types.沉淀.sensory_density提升至"极高"，增加心理深度和环境烘托；narrative.primary_driver改为"悬念推进" |
| 都市/言情 | dialogue.ratio提升至"30-40%"，增加神态细节描写；psychological_rendering.direct_thought提升至60% |
| 科幻 | metaphor.type增加"科技隐喻"子类，sensory增加"未来感描述"；worldbuilding增加"科技设定碎片化插入" |
| 历史 | narrative.tense保持过去时，增加时代特色词汇；dialogue.style.ancient使用半文半白 |
| 末世/生存 | sensory增加"危机感氛围"，pacing.rhythm_principles.default改为"持续紧张，间歇释放" |

### 步骤3：主角语音系统定制
根据主角性格 `{{protagonist_personality}}` 定制：

**主角性格映射表**：
| 性格类型 | narrative.voice定制 | dialogue.character_specific |
|----------|---------------------|----------------------------|
| 坚韧 | 沉稳中带锋芒，逆境中保持冷静观察 | 说话简洁有力，关键时刻爆发式发言 |
| 狡猾 | 机敏多变，善于隐藏真实意图 | 话中有话，常用反问和暗示 |
| 冷静 | 理性分析优先，情绪内敛 | 语速平稳，多用逻辑连接词 |
| 热血 | 情绪外放，行动力强 | 口头禅多，语气词丰富，直接表达 |
| 腹黑 | 表面温和，内心算计 | 表面客气，关键处暗藏机锋 |
| 傲娇 | 内心柔软，外表强硬 | 口是心非，否认式表达 |

**必写字段**：
- `character_voice.catchphrases`: 主角的3-5个口头禅
- `character_voice.speech_pattern`: 说话风格描述
- `character_voice.internal_monologue_style`: 内心独白风格

### 步骤4：平台适配
根据 `{{target_platform}}` 调整：

| 平台 | 调整重点 |
|------|----------|
| 番茄 | 强情绪、快节奏、多冲突、爽点密集；避免慢热和压抑 |
| 起点 | 世界观完整、升级感、长期铺垫；避免逻辑漏洞和人设崩塌 |
| 七猫 | 情感细腻、节奏适中；避免过于复杂的设定 |
| 飞卢 | 极致爽感、快节奏、创意脑洞；避免压抑超过3章 |

### 步骤5：字数阈值设置（强制）
必须显式设置以下字段，且满足 `min <= target <= max`：

```json
{
  "quality_thresholds": {
    "chapter_length": {
      "min": 2000,
      "ideal": "2500-3500",
      "max": 5000
    },
    "engagement_metrics": {
      "hook_density": "章节整体要有持续吸引力，不要求机械打点",
      "conflict_presence": "每章需要冲突、张力或关系变化中的至少一种"
    }
  }
}
```

### 步骤6：人味约束（强制）
必须补充 `humanity_signals`，用于约束草稿阶段的表达倾向：

```json
{
  "humanity_signals": {
    "max_abstract_emotion_per_1k": 6,
    "max_explanation_per_1k": 10,
    "principle": "用简单语言输出最真实情感，能用细节就不用抽象词，能让人物自己露出来就不要旁白解释"
  }
}
```

## 输出格式（必须严格遵守）

输出有效的 JSON 格式声音配置，结构如下：

```json
{
  "_meta": {
    "version": "4.0-webnovel",
    "description": "为{{genre}}题材定制的声音配置",
    "target_platform": "{{target_platform}}",
    "world_atmosphere": "{{world_atmosphere}}",
    "protagonist_personality": "{{protagonist_personality}}"
  },
  "narrative": {
    "voice": "...",
    "primary_driver": "...",
    "secondary_driver": "...",
    "writing_mode": "..."
  },
  "pacing": {
    "rhythm_principles": {...},
    "scene_structure": {...}
  },
  "description": {
    "literary_quality": {...},
    "sensory_system": {...},
    "psychological_rendering": {...}
  },
  "dialogue": {
    "density": "...",
    "target_ratio": "...",
    "character_specific": "..."
  },
  "character_voice": {
    "catchphrases": [...],
    "speech_pattern": "...",
    "internal_monologue_style": "..."
  },
  "humanity_signals": {
    "max_abstract_emotion_per_1k": 6,
    "max_explanation_per_1k": 10,
    "principle": "..."
  },
  "author_signature": {
    "tone": ["..."],
    "humor": { "enabled": true, "style": "...", "density": "medium" },
    "mature_content": { "enabled": true, "level": "mild", "boundaries": [], "avoid": [] },
    "daily_life_texture": true
  },
  "mature_content_policy": {
    "platform_safe": true,
    "reminder_only": true,
    "summary": "..."
  },
  "quality_thresholds": {
    "chapter_length": {
      "min": 2000,
      "ideal": "2500-3500",
      "max": 5000
    }
  }
}
```

## 注意事项

1. **必须输出有效JSON**：确保所有引号、逗号、括号正确闭合
2. **不要输出Markdown代码块标记**：直接输出JSON内容
3. **根据世界观调整**：如果世界观中有特殊的修炼体系、科技设定等，应在相应章节体现
4. **保持灵活性**：规则是参考不是枷锁，根据剧情需要可以打破
