"""
Relationship Validator - 角色关系一致性检查器 (v1.4.0)

负责：
- 关系类型与指标一致性检查
- 阵营冲突检测
- 三角关系发现
- 角色行为与关系一致性验证
"""
from typing import Any, Dict, List, Optional
from collections import defaultdict


class RelationshipValidator:
    def __init__(self, relationship_manager):
        self.rm = relationship_manager
    
    def validate(self, chapter_num: int, check_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        全面检查角色关系一致性
        
        Args:
            chapter_num: 当前章节号
            check_types: 检查类型列表（如 ["faction_conflict", "triangular"]）
        
        Returns:
            验证结果
        """
        issues = []
        warnings = []
        
        # 1. 检查关系指标与类型是否匹配
        issues.extend(self._validate_type_metrics_consistency())
        
        # 2. 检查双向关系一致性
        issues.extend(self._validate_bidirectional_consistency())
        
        # 3. 检查阵营冲突
        faction_issues = self._validate_faction_conflicts()
        issues.extend([i for i in faction_issues if i.get("severity") == "critical"])
        warnings.extend([i for i in faction_issues if i.get("severity") == "warning"])
        
        # 4. 检查三角关系
        triangles = self._detect_triangular_relationships()
        if triangles:
            warnings.append({
                "code": "triangular_relationships_detected",
                "count": len(triangles),
                "triangles": triangles,
                "severity": "info",
            })
        
        # 5. 检查角色行为与关系一致性（需要章节内容）
        # issues.extend(self._validate_behavior_consistency(chapter_num))
        
        return {
            "valid": len([i for i in issues if i.get("severity") == "critical"]) == 0,
            "issues": issues,
            "warnings": warnings,
            "chapter": chapter_num,
        }
    
    def _validate_type_metrics_consistency(self) -> List[Dict[str, Any]]:
        """
        检查关系类型与指标是否匹配
        例如：恋人关系的亲密度应在 80-100 之间
        """
        issues = []
        relationships = self.rm.list_relationships()
        
        for rel in relationships:
            rel_type = rel.get("type")
            metrics = rel.get("metrics", {})
            type_def = self.rm._find_type_definition(rel_type)
            
            if not type_def:
                continue
            
            # 检查亲密度范围
            intimacy_range = type_def.get("intimacy_range")
            if intimacy_range:
                intimacy = metrics.get("intimacy", 0)
                if intimacy < intimacy_range[0] or intimacy > intimacy_range[1]:
                    issues.append({
                        "code": "metrics_type_mismatch",
                        "relationship": rel["id"],
                        "characters": [rel["character_a"], rel["character_b"]],
                        "type": rel_type,
                        "message": f"关系类型'{rel_type}'的亲密度应为{intimacy_range}，实际为{intimacy}",
                        "severity": "warning",
                        "suggestion": f"调整亲密度至{intimacy_range[0]}-{intimacy_range[1]}范围，或更改关系类型",
                    })
            
            # 检查信任度最低要求
            trust_min = type_def.get("trust_min")
            if trust_min is not None:
                trust = metrics.get("trust", 0)
                if trust < trust_min:
                    issues.append({
                        "code": "trust_below_minimum",
                        "relationship": rel["id"],
                        "characters": [rel["character_a"], rel["character_b"]],
                        "type": rel_type,
                        "message": f"关系类型'{rel_type}'的信任度应≥{trust_min}，实际为{trust}",
                        "severity": "warning",
                        "suggestion": f"提升信任度至{trust_min}以上，或更改关系类型",
                    })
        
        return issues
    
    def _validate_bidirectional_consistency(self) -> List[Dict[str, Any]]:
        """
        检查双向关系的一致性
        """
        issues = []
        relationships = self.rm.list_relationships()
        
        for rel in relationships:
            if not rel.get("bidirectional"):
                continue
            
            # 双向关系应该有反向类型
            if not rel.get("reverse_type"):
                issues.append({
                    "code": "missing_reverse_type",
                    "relationship": rel["id"],
                    "message": f"双向关系 {rel['id']} 缺少反向类型定义",
                    "severity": "warning",
                    "suggestion": "设置 reverse_type 字段",
                })
        
        return issues
    
    def _validate_faction_conflicts(self) -> List[Dict[str, Any]]:
        """
        检查阵营冲突
        例如：同一阵营的成员不应是死敌关系
        """
        issues = []
        factions = self.rm.list_factions()
        
        for faction in factions:
            faction_id = faction["id"]
            faction_name = faction["name"]
            members = faction.get("members", [])
            enemies = faction.get("enemies", [])
            
            # 1. 检查成员之间是否有敌对关系
            for i, member_a in enumerate(members):
                for member_b in members[i+1:]:
                    rel = self.rm.get_relationship_between(member_a, member_b)
                    if rel and rel.get("type") in ["enemy", "traitor"]:
                        issues.append({
                            "code": "faction_internal_conflict",
                            "faction": faction_name,
                            "faction_id": faction_id,
                            "characters": [member_a, member_b],
                            "relationship_type": rel["type"],
                            "message": f"阵营「{faction_name}」成员 {member_a} 和 {member_b} 是{rel['type']}关系",
                            "severity": "warning",
                            "suggestion": "确认是否为剧情需要（如卧底），如是需要更新关系状态或添加备注",
                        })
            
            # 2. 检查成员与敌对阵营成员是否有友好关系
            for enemy_faction_id in enemies:
                enemy_faction = self.rm.get_faction(enemy_faction_id)
                if not enemy_faction:
                    continue
                
                for member in members:
                    for enemy_member in enemy_faction.get("members", []):
                        rel = self.rm.get_relationship_between(member, enemy_member)
                        if rel and rel.get("type") in ["lover", "best_friend", "ally"]:
                            issues.append({
                                "code": "cross_faction_conflict",
                                "faction": faction_name,
                                "enemy_faction": enemy_faction["name"],
                                "characters": [member, enemy_member],
                                "relationship_type": rel["type"],
                                "message": f"{member}（{faction_name}）与敌对阵营成员{enemy_member}（{enemy_faction['name']}）有{rel['type']}关系",
                                "severity": "critical",
                                "suggestion": "这是潜在的剧情冲突点，确认是否为剧情需要",
                            })
        
        return issues
    
    def _detect_triangular_relationships(self) -> List[Dict[str, Any]]:
        """
        检测三角关系（潜在剧情冲突点）
        """
        triangles = []
        relationships = self.rm.list_relationships(status="active")
        
        # 构建关系图
        graph = defaultdict(dict)
        for rel in relationships:
            char_a = rel["character_a"]
            char_b = rel["character_b"]
            rel_type = rel["type"]
            intimacy = rel.get("metrics", {}).get("intimacy", 0)
            
            graph[char_a][char_b] = {"type": rel_type, "intimacy": intimacy}
            if rel.get("bidirectional", False):
                reverse_type = rel.get("reverse_type", rel_type)
                graph[char_b][char_a] = {"type": reverse_type, "intimacy": intimacy}
        
        # 查找三角关系
        characters = list(graph.keys())
        found_triangles = set()
        
        for i, char_a in enumerate(characters):
            for char_b in graph[char_a]:
                if char_b in characters[i+1:]:
                    for char_c in characters:
                        if char_c != char_a and char_c != char_b:
                            if char_c in graph[char_a] and char_c in graph[char_b]:
                                # 发现三角关系
                                triangle_chars = tuple(sorted([char_a, char_b, char_c]))
                                if triangle_chars in found_triangles:
                                    continue
                                found_triangles.add(triangle_chars)
                                
                                triangle = {
                                    "characters": list(triangle_chars),
                                    "relationships": {
                                        f"{char_a}-{char_b}": graph[char_a][char_b],
                                        f"{char_a}-{char_c}": graph[char_a][char_c],
                                        f"{char_b}-{char_c}": graph[char_b][char_c],
                                    }
                                }
                                
                                # 判断是否为情感三角（潜在冲突）
                                if self._is_romantic_triangle(triangle):
                                    triangle["conflict_type"] = "romantic_triangle"
                                    triangle["drama_potential"] = "high"
                                elif self._is_loyalty_triangle(triangle):
                                    triangle["conflict_type"] = "loyalty_conflict"
                                    triangle["drama_potential"] = "medium"
                                else:
                                    triangle["conflict_type"] = "general"
                                    triangle["drama_potential"] = "low"
                                
                                triangles.append(triangle)
        
        return triangles
    
    def _is_romantic_triangle(self, triangle: Dict[str, Any]) -> bool:
        """
        判断是否为情感三角关系
        """
        rels = triangle["relationships"].values()
        romantic_types = ["lover", "crush", "ex_lover", "arranged_marriage"]
        
        romantic_count = sum(1 for r in rels if r["type"] in romantic_types)
        return romantic_count >= 2
    
    def _is_loyalty_triangle(self, triangle: Dict[str, Any]) -> bool:
        """
        判断是否为忠诚度冲突三角
        """
        rels = triangle["relationships"].values()
        hierarchy_types = ["master", "apprentice", "senior", "junior", "superior", "subordinate"]
        
        hierarchy_count = sum(1 for r in rels if r["type"] in hierarchy_types)
        return hierarchy_count >= 2
    
    def detect_conflicts(self, character_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        检测特定角色或所有角色的关系冲突
        
        Args:
            character_id: 角色 ID（可选，不传则检测所有）
        
        Returns:
            冲突列表
        """
        conflicts = []
        
        # 获取三角关系
        triangles = self._detect_triangular_relationships()
        for triangle in triangles:
            if character_id is None or character_id in triangle["characters"]:
                conflicts.append({
                    "type": triangle["conflict_type"],
                    "characters": triangle["characters"],
                    "drama_potential": triangle["drama_potential"],
                    "description": f"检测到{'情感' if triangle['conflict_type'] == 'romantic_triangle' else '忠诚度'}三角关系",
                })
        
        # 获取阵营冲突
        faction_issues = self._validate_faction_conflicts()
        for issue in faction_issues:
            if issue.get("severity") == "critical":
                if character_id is None or any(character_id in issue.get("characters", []) for character_id in [character_id] if character_id):
                    conflicts.append({
                        "type": "faction_conflict",
                        "characters": issue.get("characters"),
                        "faction": issue.get("faction"),
                        "description": issue.get("message"),
                    })
        
        return conflicts
