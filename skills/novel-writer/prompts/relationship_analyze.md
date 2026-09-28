# 任务：分析角色关系并生成剧情推荐

## 输入信息

- **当前章节**: {{chapter_num}}
- **章节大纲**: {{chapter_outline}}
- **涉及角色**: {{involved_characters}}
- **现有关系网络**: {{relationship_network}}
- ** detected_conflicts**: {{detected_conflicts}}
- **世界观**: {{world_hooks}}
- **声音配置**: {{voice_config}}

## 分析维度

### 1. 关系一致性检查

检查章节中角色的行为是否与现有关系一致：

| 检查项 | 说明 |
|--------|------|
| 朋友互动 | 朋友之间是否互相帮助、信任？ |
| 敌人对立 | 敌人之间是否有冲突、对抗？ |
| 恋人情感 | 恋人之间是否有情感互动、关心？ |
| 师徒关系 | 师徒之间是否有教导、尊重？ |
| 阵营忠诚 | 成员是否对阵营忠诚？ |

**发现不一致时**：提示用户确认是否为剧情需要，如是需要建议更新关系状态。

### 2. 关系发展机会

识别本章可发展的关系：

| 触发条件 | 发展类型 | 建议场景 |
|----------|----------|----------|
| 共同经历危险 | 亲密度提升 | 生死关头的告白 |
| 理念冲突 | 关系恶化 | 争吵、决裂 |
| 误会解开 | 信任度提升 | 和解、拥抱 |
| 利益冲突 | 背叛预警 | 暗中交易、背叛 |
| 长期相处 | 友情→爱情 | 暧昧互动、嫉妒 |

### 3. 潜在冲突检测

发现潜在的关系冲突：

| 冲突类型 | 识别条件 | 戏剧潜力 |
|----------|----------|----------|
| 三角关系 | A→B, B→C, C→A 的情感连接 | high |
| 阵营对立 | 敌对阵营成员的友好关系 | high |
| 忠诚度冲突 | 师徒/上下级之间的复杂关系 | medium |
| 身份矛盾 | 双重身份导致的冲突 | high |

### 4. 剧情推荐生成

基于关系状态生成具体剧情建议：

#### 推荐类型

| 类型 | 触发条件 | 示例场景 |
|------|----------|----------|
| conflict_escalation | 三角关系、误会 | 当面对质、被迫选择 |
| loyalty_test | 阵营冲突、师徒关系 | 被迫站队、暗中帮助 |
| relationship_upgrade | 亲密度达标 | 告白、关系确认 |
| relationship_turn | 敌对关系缓和 | 化敌为友、合作 |
| betrayal_warning | 信任度偏低 | 背叛、揭露 |

## 输出格式

```json
{
  "consistency_check": {
    "passed": true,
    "issues": [
      {
        "code": "behavior_relationship_mismatch",
        "characters": ["A", "B"],
        "message": "A 帮助了 B，但两人是敌人关系",
        "severity": "warning",
        "suggestion": "确认是否为卧底剧情，如是需要更新关系类型"
      }
    ]
  },
  "relationship_changes": [
    {
      "relationship_id": "protagonist_li_si",
      "change_type": "intimacy_increase",
      "reason": "共同对抗敌人",
      "metrics_change": {
        "intimacy": 10,
        "trust": 5
      },
      "suggested_event": "李四为主角挡下一击"
    }
  ],
  "potential_conflicts": [
    {
      "type": "romantic_triangle",
      "characters": ["protagonist", "li_si", "xiao_mei"],
      "description": "小美暗恋主角，但主角与李四是挚友",
      "drama_potential": "high",
      "recommended_scenes": [
        "误会加深",
        "当面对质",
        "被迫选择"
      ]
    }
  ],
  "plot_recommendations": [
    {
      "type": "loyalty_test",
      "subtype": "cross_faction_romance",
      "title": "跨阵营恋情危机",
      "characters": ["protagonist", "villain_daughter"],
      "description": "主角与反派女儿的恋情面临阵营压力",
      "suggested_scenes": [
        {
          "name": "秘密会面",
          "description": "两人避开阵营耳目私下见面",
          "emotional_intensity": 8
        },
        {
          "name": "战场相遇",
          "description": "在战场上被迫对立",
          "emotional_intensity": 9
        }
      ],
      "drama_potential": "high",
      "chapter_suitability": 25
    }
  ],
  "emotional_arc_suggestion": [
    "平静开场",
    "冲突预兆",
    "矛盾升级",
    "情绪爆发",
    "短暂缓和",
    "新的危机"
  ]
}
```

## 处理流程

1. **加载关系数据**: 从 relationship_network 获取当前关系状态
2. **一致性检查**: 对比章节大纲中的角色行为与关系定义
3. **冲突检测**: 调用 detect_conflicts 识别潜在冲突
4. **推荐生成**: 基于冲突和关系阶段生成剧情推荐
5. **排序过滤**: 按戏剧潜力排序，返回 top 推荐

## 注意事项

1. **推荐质量优先**: 只推荐真正有戏剧潜力的情节，避免为了推荐而推荐
2. **尊重用户创作**: 推荐是建议不是强制，用户可以选择忽略
3. **保持一致性**: 推荐应符合世界观和角色性格
4. **适度惊喜**: 可以推荐一些意想不到的发展，但要合理

## 示例调用

```python
# 分析第 25 章的关系剧情
result = analyze_relationships(
    chapter_num=25,
    chapter_outline="主角与李四共同对抗魔教，发现魔教圣女竟是昔日恋人",
    involved_characters=["protagonist", "li_si", "sheng_nv"],
    relationship_network={...},
    detected_conflicts=[...]
)

# 获取推荐
for rec in result["plot_recommendations"]:
    print(f"推荐：{rec['title']}")
    print(f"  类型：{rec['type']}")
    print(f"  戏剧潜力：{rec['drama_potential']}")
```
