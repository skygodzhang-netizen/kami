"""
Plot Recommender - 基于角色关系的剧情推荐引擎 (v1.4.0)

负责：
- 基于关系冲突推荐剧情发展
- 生成关系演变场景建议
- 识别戏剧潜力高的关系组合
- 提供忠诚度考验、情感爆发等经典桥段
"""
from typing import Any, Dict, List, Optional
from collections import defaultdict


class PlotRecommender:
    def __init__(self, relationship_manager, relationship_validator):
        self.rm = relationship_manager
        self.validator = relationship_validator
    
    def recommend(self, character_id: Optional[str] = None, 
                  chapter_num: int = 1,
                  focus_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        基于角色关系推荐剧情发展
        
        Args:
            character_id: 聚焦的角色 ID（可选，不传则分析所有）
            chapter_num: 当前章节号
            focus_types: 关注的推荐类型（如 ["conflict", "romance", "loyalty"]）
        
        Returns:
            推荐列表
        """
        recommendations = []
        
        # 1. 检测冲突
        conflicts = self.validator.detect_conflicts(character_id)
        
        # 2. 基于冲突生成推荐
        for conflict in conflicts:
            rec = self._conflict_to_recommendation(conflict, chapter_num)
            if rec and (not focus_types or rec["type"] in focus_types):
                recommendations.append(rec)
        
        # 3. 分析关系发展阶段
        stage_recs = self._analyze_relationship_stages(character_id, chapter_num)
        for rec in stage_recs:
            if not focus_types or rec["type"] in focus_types:
                recommendations.append(rec)
        
        # 4. 识别潜在戏剧点
        drama_recs = self._identify_drama_potential(character_id, chapter_num)
        for rec in drama_recs:
            if not focus_types or rec["type"] in focus_types:
                recommendations.append(rec)
        
        # 按戏剧潜力排序
        recommendations.sort(key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(x.get("drama_potential", "low"), 0), reverse=True)
        
        return {
            "chapter": chapter_num,
            "character_focus": character_id,
            "recommendations": recommendations,
            "count": len(recommendations),
        }
    
    def _conflict_to_recommendation(self, conflict: Dict[str, Any], chapter_num: int) -> Optional[Dict[str, Any]]:
        """将冲突转换为剧情推荐"""
        conflict_type = conflict.get("type")
        
        if conflict_type == "romantic_triangle":
            chars = conflict.get("characters", [])
            return {
                "type": "conflict_escalation",
                "subtype": "romantic_triangle",
                "title": "三角关系爆发",
                "characters": chars,
                "description": f"{chars[0]}, {chars[1]}, {chars[2]} 之间的三角关系可在此章爆发冲突",
                "suggested_scenes": [
                    {"name": "误会加深", "description": "因信息不对称导致误会升级"},
                    {"name": "当面对质", "description": "三方齐聚，情绪爆发"},
                    {"name": "被迫选择", "description": "主角必须在两人之间做出选择"},
                    {"name": "意外揭露", "description": "隐藏的感情被意外曝光"}
                ],
                "drama_potential": "high",
                "emotional_intensity": 9,
                "chapter_suitability": chapter_num,
            }
        
        elif conflict_type == "loyalty_conflict":
            chars = conflict.get("characters", [])
            return {
                "type": "loyalty_test",
                "subtype": "hierarchy_conflict",
                "title": "忠诚度考验",
                "characters": chars,
                "description": f"角色面临阵营/师徒关系与个人情感的冲突",
                "suggested_scenes": [
                    {"name": "被迫站队", "description": "必须在对立的双方中选择一方"},
                    {"name": "暗中帮助", "description": "偷偷帮助敌对阵营的亲友"},
                    {"name": "身份暴露危机", "description": "双重身份险些暴露"},
                    {"name": "理念冲突", "description": "与师长/上级因理念产生分歧"}
                ],
                "drama_potential": "high",
                "emotional_intensity": 8,
                "chapter_suitability": chapter_num,
            }
        
        elif conflict_type == "faction_conflict":
            chars = conflict.get("characters", [])
            faction = conflict.get("faction", "")
            return {
                "type": "faction_crisis",
                "subtype": "cross_faction_romance",
                "title": "跨阵营恋情危机",
                "characters": chars,
                "description": conflict.get("description", ""),
                "suggested_scenes": [
                    {"name": "秘密会面", "description": "两人避开阵营耳目私下见面"},
                    {"name": "阵营压力", "description": "来自阵营内部的压力和质疑"},
                    {"name": "战场相遇", "description": "在战场上被迫对立"},
                    {"name": "私奔计划", "description": "考虑放弃阵营私奔"}
                ],
                "drama_potential": "high",
                "emotional_intensity": 9,
                "chapter_suitability": chapter_num,
            }
        
        return None
    
    def _analyze_relationship_stages(self, character_id: Optional[str], chapter_num: int) -> List[Dict[str, Any]]:
        """分析关系发展阶段并推荐"""
        recommendations = []

        relationship_entries = self._collect_stage_relationships(character_id)
        for rel_info in relationship_entries:
            primary_character = rel_info.get("primary_character")
            other_id = rel_info.get("other_character")
            rel_type = rel_info.get("type", "")
            metrics = rel_info.get("metrics", {})
            intimacy = metrics.get("intimacy", 50)
            trust = metrics.get("trust", 50)
            
            # 友情→爱情发展
            if rel_type == "friend" and 70 <= intimacy < 85 and primary_character and other_id:
                recommendations.append({
                    "type": "relationship_upgrade",
                    "subtype": "friend_to_lover",
                    "title": "友情升华为爱情",
                    "characters": [primary_character, other_id],
                    "description": f"{primary_character}与{other_id}的友情可进一步发展",
                    "suggested_scenes": [
                        {"name": "生死关头的告白", "description": "在危险时刻表达真实感情"},
                        {"name": "酒后吐真言", "description": "借酒劲说出心里话"},
                        {"name": "误会后的和解", "description": "误会解除后感情升温"},
                        {"name": "嫉妒触发", "description": "看到对方与他人亲近产生嫉妒"}
                    ],
                    "drama_potential": "medium",
                    "emotional_intensity": 7,
                    "readiness_score": intimacy / 10,
                })
            
            # 敌对→和解
            if rel_type == "enemy" and intimacy > -30 and primary_character and other_id:
                recommendations.append({
                    "type": "relationship_turn",
                    "subtype": "enemy_to_ally",
                    "title": "化敌为友",
                    "characters": [primary_character, other_id],
                    "description": f"{primary_character}与{other_id}的敌对关系可出现转机",
                    "suggested_scenes": [
                        {"name": "共同抗敌", "description": "面对更强敌人被迫合作"},
                        {"name": "救命之恩", "description": "对方在关键时刻救了自己"},
                        {"name": "误会解除", "description": "发现敌对是基于误会"},
                        {"name": "利益一致", "description": "发现双方目标其实一致"}
                    ],
                    "drama_potential": "high",
                    "emotional_intensity": 8,
                    "readiness_score": (intimacy + 100) / 20,
                })
            
            # 师徒关系突破
            if rel_type == "master" and intimacy > 80 and trust > 75 and primary_character and other_id:
                recommendations.append({
                    "type": "relationship_deepening",
                    "subtype": "master_apprentice_bond",
                    "title": "师徒情深",
                    "characters": [primary_character, other_id],
                    "description": f"{primary_character}与师父{other_id}的关系可进一步深化",
                    "suggested_scenes": [
                        {"name": "倾囊相授", "description": "师父传授绝学"},
                        {"name": "为师报仇", "description": "师父遇害后主角复仇"},
                        {"name": "青出于蓝", "description": "徒弟超越师父"},
                        {"name": "遗愿传承", "description": "师父临终托付"}
                    ],
                    "drama_potential": "medium",
                    "emotional_intensity": 7,
                    "readiness_score": (intimacy + trust) / 20,
                })
            
            # 背叛预警
            if rel_type in ["best_friend", "ally"] and trust < 40 and primary_character and other_id:
                recommendations.append({
                    "type": "betrayal_warning",
                    "subtype": "trust_crisis",
                    "title": "背叛预警",
                    "characters": [primary_character, other_id],
                    "description": f"{primary_character}与{other_id}的信任度偏低，可能发生背叛",
                    "suggested_scenes": [
                        {"name": "利益诱惑", "description": "对方因利益动摇"},
                        {"name": "秘密发现", "description": "发现对方隐藏的秘密"},
                        {"name": "被迫背叛", "description": "对方被要挟背叛主角"},
                        {"name": "理念分歧", "description": "因理念不同走向对立"}
                    ],
                    "drama_potential": "high",
                    "emotional_intensity": 9,
                    "urgency": "high",
                })
        
        return recommendations

    def _collect_stage_relationships(self, character_id: Optional[str]) -> List[Dict[str, Any]]:
        if character_id:
            relationships = self.rm.get_character_relationships(character_id)
            return [
                {
                    "primary_character": character_id,
                    "other_character": other_id,
                    "type": rel_info.get("type"),
                    "metrics": rel_info.get("metrics", {}),
                }
                for other_id, rel_info in relationships.items()
            ]

        relationship_entries = []
        for rel in self.rm.list_relationships():
            relationship_entries.append(
                {
                    "primary_character": rel.get("character_a"),
                    "other_character": rel.get("character_b"),
                    "type": rel.get("type"),
                    "metrics": rel.get("metrics", {}),
                }
            )

            reverse_type = rel.get("reverse_type") or rel.get("type")
            if rel.get("character_a") != rel.get("character_b"):
                relationship_entries.append(
                    {
                        "primary_character": rel.get("character_b"),
                        "other_character": rel.get("character_a"),
                        "type": reverse_type,
                        "metrics": rel.get("metrics", {}),
                    }
                )

        return relationship_entries
    
    def _identify_drama_potential(self, character_id: Optional[str], chapter_num: int) -> List[Dict[str, Any]]:
        """识别潜在戏剧点"""
        recommendations = []
        
        # 获取关系网络
        network = self.rm.get_relationship_network()
        
        # 查找高亲密度但未定义关系类型的角色对
        for rel in network.get("relationships", []):
            if character_id and character_id not in [rel["character_a"], rel["character_b"]]:
                continue
            
            metrics = rel.get("metrics", {})
            intimacy = metrics.get("intimacy", 0)
            rel_type = rel.get("type", "")
            
            # 高亲密度但关系类型模糊
            if intimacy > 80 and rel_type in ["friend", "acquaintance"]:
                chars = [rel["character_a"], rel["character_b"]]
                recommendations.append({
                    "type": "relationship_definition",
                    "subtype": "ambiguous_relationship",
                    "title": "关系定义",
                    "characters": chars,
                    "description": f"{chars[0]}与{chars[1]}亲密度很高，但关系类型未明确",
                    "suggested_scenes": [
                        {"name": "关系确认", "description": "通过事件明确关系定位"},
                        {"name": "第三方触发", "description": "因第三方介入迫使关系明确"},
                        {"name": "自然发展", "description": "水到渠成升级关系"}
                    ],
                    "drama_potential": "medium",
                    "emotional_intensity": 6,
                })
        
        # 查找长期未更新的关系
        # (需要历史记录支持，当前简化实现)
        
        return recommendations
    
    def generate_scene_outline(self, recommendation: Dict[str, Any], 
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        基于推荐生成详细场景大纲
        
        Args:
            recommendation: 推荐对象
            context: 额外上下文（如世界观、当前剧情）
        
        Returns:
            场景大纲
        """
        scene = recommendation.get("suggested_scenes", [{}])[0]
        
        outline = {
            "title": recommendation["title"],
            "type": recommendation["type"],
            "characters": recommendation.get("characters", []),
            "scene_name": scene.get("name", "未命名场景"),
            "scene_description": scene.get("description", ""),
            "emotional_arc": self._generate_emotional_arc(recommendation),
            "key_beats": self._generate_key_beats(recommendation),
            "dialogue_hints": self._generate_dialogue_hints(recommendation),
        }
        
        if context:
            outline["world_context"] = context.get("world_hooks", "")
            outline["voice_config"] = context.get("voice_config", {})
        
        return outline
    
    def _generate_emotional_arc(self, recommendation: Dict[str, Any]) -> List[str]:
        """生成情绪弧线"""
        intensity = recommendation.get("emotional_intensity", 5)
        
        if intensity >= 8:
            return [
                "平静开场",
                "冲突预兆",
                "矛盾升级",
                "情绪爆发",
                "短暂缓和",
                "新的危机"
            ]
        elif intensity >= 6:
            return [
                "日常铺垫",
                "微妙变化",
                "情感积累",
                "温和爆发",
                "关系深化"
            ]
        else:
            return [
                "平静发展",
                "小插曲",
                "关系推进"
            ]
    
    def _generate_key_beats(self, recommendation: Dict[str, Any]) -> List[str]:
        """生成关键节拍"""
        rec_type = recommendation.get("type", "")
        
        beat_templates = {
            "conflict_escalation": [
                "触发事件：误会产生",
                "升级：信息不对称加剧",
                "转折：真相一角揭露",
                "高潮：当面对质",
                "余波：关系重新定义"
            ],
            "loyalty_test": [
                "两难处境出现",
                "内心挣扎",
                "初步选择",
                "代价显现",
                "后果承担"
            ],
            "relationship_upgrade": [
                "日常互动铺垫",
                "特殊事件触发",
                "情感表达",
                "关系确认",
                "新的开始"
            ],
            "betrayal_warning": [
                "异常行为出现",
                "主角察觉但忽视",
                "线索积累",
                "背叛发生",
                "主角反应"
            ]
        }
        
        return beat_templates.get(rec_type, ["情节发展", "冲突出现", "解决方案"])
    
    def _generate_dialogue_hints(self, recommendation: Dict[str, Any]) -> List[str]:
        """生成对话提示"""
        rec_type = recommendation.get("type", "")
        
        hints = {
            "conflict_escalation": [
                "你为什么不相信我？",
                "我从来不知道你是这样的人",
                "事情不是你想的那样...",
                "够了！我不想再听解释"
            ],
            "loyalty_test": [
                "对不起，我有自己的立场",
                "你明白我的处境吗？",
                "如果可以，我也不想这样",
                "这是唯一的选择"
            ],
            "relationship_upgrade": [
                "其实我一直想告诉你...",
                "你对我来说很重要",
                "我不想失去你",
                "我们...可以试试"
            ],
            "betrayal_warning": [
                "对不起",
                "我也有苦衷",
                "这是为了大局",
                "希望你能理解"
            ]
        }
        
        return hints.get(rec_type, ["对话内容"])
