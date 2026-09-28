"""
Relationship Manager - 角色关系管理模块 (v1.4.0)

负责：
- 角色关系的 CRUD 操作
- 关系演变历史记录
- 关系查询与过滤
- 阵营管理
"""
import json
import tempfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class RelationshipManager:
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        try:
            from .project_layout import ProjectLayout
        except ImportError:
            from project_layout import ProjectLayout
        self.layout = ProjectLayout(self.run_dir)
        self._relationship_types = self._load_relationship_types()

    def _character_cards_path(self) -> Path:
        resolved = self.layout.resolve_config("character_cards")
        return resolved or self.layout.config_path("character_cards")
    
    def _load_relationships_data(self) -> Dict[str, Any]:
        """加载关系数据"""
        path = self._character_cards_path()
        return self._load_json_at(path, {"characters": {}, "relationships": {}, "factions": {}})

    def _save_relationships_data(self, data: Dict[str, Any]) -> None:
        """保存关系数据"""
        self._save_json_at(self._character_cards_path(), data)
    
    def _load_json(self, file_name: str, default: Any) -> Any:
        """加载 JSON 文件（兼容旧接口）"""
        if file_name == "character_cards.json":
            return self._load_relationships_data()
        path = self.run_dir / file_name
        return self._load_json_at(path, default)

    def _load_json_at(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return deepcopy(default)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to load {path}: {e}")
            return deepcopy(default)

    def _save_json(self, file_name: str, data: Any) -> None:
        if file_name == "character_cards.json":
            self._save_relationships_data(data)
            return
        self._save_json_at(self.run_dir / file_name, data)

    def _save_json_at(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as temp_file:
            temp_file.write(payload)
            temp_path = temp_file.name
        import os
        os.replace(temp_path, path)

    def _load_relationship_types(self) -> Dict[str, Any]:
        """加载关系类型定义"""
        types_path = Path(__file__).resolve().parent.parent / "relationship_types.json"
        if types_path.exists():
            try:
                with open(types_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to load relationship types: {e}")
        return {}
    
    def _generate_relationship_id(self, char_a: str, char_b: str) -> str:
        """生成关系 ID（按字母顺序确保唯一性）"""
        chars = sorted([char_a, char_b])
        return f"{chars[0]}_{chars[1]}"
    
    def _get_timestamp(self) -> str:
        """获取 ISO 时间戳"""
        return datetime.now().isoformat()
    
    def _find_type_definition(self, rel_type: str) -> Optional[Dict[str, Any]]:
        """根据关系类型 ID 查找定义"""
        for category in self._relationship_types.values():
            for type_def in category.get("types", []):
                if type_def["id"] == rel_type:
                    return type_def
        return None

    def _resolve_reverse_type(self, rel_type: str, type_def: Optional[Dict[str, Any]] = None) -> Optional[str]:
        type_def = type_def or self._find_type_definition(rel_type)
        if not type_def:
            return rel_type
        return type_def.get("reverse_type") or rel_type
    
    # ==================== 关系 CRUD ====================
    
    def create_relationship(
        self,
        character_a: str,
        character_b: str,
        rel_type: str,
        metrics: Optional[Dict[str, Any]] = None,
        since_chapter: Optional[int] = None,
        bidirectional: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        创建角色关系
        
        Args:
            character_a: 角色 A ID
            character_b: 角色 B ID
            rel_type: 关系类型（如 "friend", "lover", "enemy"）
            metrics: 关系指标（intimacy, trust, conflict 等）
            since_chapter: 关系建立的章节号
            bidirectional: 是否双向关系（如未指定则根据类型自动判断）
        
        Returns:
            创建的关系对象
        """
        if character_a == character_b:
            raise ValueError("不能创建自引用关系")
        
        data = self._load_relationships_data()
        
        # 检查是否已存在
        rel_id = self._generate_relationship_id(character_a, character_b)
        if rel_id in data.get("relationships", {}):
            raise ValueError(f"关系 {rel_id} 已存在，请使用 update_relationship 更新")
        
        # 获取类型定义
        type_def = self._find_type_definition(rel_type)
        if not type_def:
            print(f"[Warning] Unknown relationship type: {rel_type}")
        
        # 确定是否双向
        if bidirectional is None:
            bidirectional = type_def.get("bidirectional", True) if type_def else True
        reverse_type = self._resolve_reverse_type(rel_type, type_def)
        
        # 默认指标
        default_metrics = {
            "intimacy": 50,
            "trust": 50,
            "conflict": 0,
        }
        if metrics:
            default_metrics.update(metrics)
        
        # 创建关系
        relationship = {
            "id": rel_id,
            "character_a": character_a,
            "character_b": character_b,
            "type": rel_type,
            "bidirectional": bidirectional,
            "reverse_type": reverse_type,
            "metrics": default_metrics,
            "history": [
                {
                    "chapter": since_chapter or 1,
                    "timestamp": self._get_timestamp(),
                    "event": "关系建立",
                    "metrics_snapshot": deepcopy(default_metrics),
                }
            ],
            "status": "active",
            "created_at": since_chapter or 1,
            "last_updated": since_chapter or 1,
        }
        
        # 验证指标范围
        if type_def:
            intimacy_range = type_def.get("intimacy_range")
            if intimacy_range:
                intimacy = default_metrics.get("intimacy", 50)
                if intimacy < intimacy_range[0] or intimacy > intimacy_range[1]:
                    print(f"[Warning] Intimacy {intimacy} outside recommended range {intimacy_range} for type {rel_type}")
        
        # 保存到数据
        if "relationships" not in data:
            data["relationships"] = {}
        data["relationships"][rel_id] = relationship
        
        # 更新角色的关系索引
        for char_id in [character_a, character_b]:
            if char_id in data.get("characters", {}):
                char_data = data["characters"][char_id]
                if "relationships" not in char_data:
                    char_data["relationships"] = {}
                other_char = character_b if char_id == character_a else character_a
                char_data["relationships"][other_char] = {
                    "type": rel_type if char_id == character_a else reverse_type,
                    "status": "active",
                    "since_chapter": since_chapter or 1,
                }
        
        self._save_relationships_data(data)
        return deepcopy(relationship)
    
    def get_relationship(self, character_a: str, character_b: str) -> Optional[Dict[str, Any]]:
        """获取两个角色之间的关系"""
        data = self._load_relationships_data()
        rel_id = self._generate_relationship_id(character_a, character_b)
        return deepcopy(data.get("relationships", {}).get(rel_id))
    
    def update_relationship(
        self,
        character_a: str,
        character_b: str,
        metrics_change: Optional[Dict[str, Any]] = None,
        event: str = "",
        chapter_num: Optional[int] = None,
        rel_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        更新角色关系
        
        Args:
            character_a: 角色 A ID
            character_b: 角色 B ID
            metrics_change: 指标变化（如 {"intimacy": 10, "trust": -5}）
            event: 变更原因描述
            chapter_num: 当前章节号
            rel_type: 新的关系类型（可选）
        
        Returns:
            更新后的关系对象
        """
        data = self._load_relationships_data()
        rel_id = self._generate_relationship_id(character_a, character_b)
        
        if rel_id not in data.get("relationships", {}):
            raise ValueError(f"关系 {rel_id} 不存在")
        
        relationship = data["relationships"][rel_id]
        
        # 更新类型
        if rel_type:
            old_type = relationship["type"]
            relationship["type"] = rel_type
            type_def = self._find_type_definition(rel_type)
            relationship["reverse_type"] = self._resolve_reverse_type(rel_type, type_def)
        
        # 更新指标
        if metrics_change:
            for key, value in metrics_change.items():
                if key in relationship["metrics"]:
                    old_value = relationship["metrics"][key]
                    relationship["metrics"][key] += value
                    
                    # 记录历史
                    history_entry = {
                        "chapter": chapter_num,
                        "timestamp": self._get_timestamp(),
                        "event": event,
                        "change": {
                            key: {
                                "from": old_value,
                                "to": relationship["metrics"][key],
                                "delta": value,
                            }
                        },
                        "metrics_snapshot": deepcopy(relationship["metrics"]),
                    }
                    relationship["history"].append(history_entry)
        
        # 更新时间
        if chapter_num:
            relationship["last_updated"] = chapter_num
        
        data["relationships"][rel_id] = relationship
        self._save_relationships_data(data)
        return deepcopy(relationship)
    
    def delete_relationship(self, character_a: str, character_b: str) -> bool:
        """删除角色关系"""
        data = self._load_relationships_data()
        rel_id = self._generate_relationship_id(character_a, character_b)
        
        if rel_id not in data.get("relationships", {}):
            return False
        
        del data["relationships"][rel_id]
        
        # 更新角色索引
        for char_id in [character_a, character_b]:
            if char_id in data.get("characters", {}):
                other_char = character_b if char_id == character_a else character_a
                if other_char in data["characters"][char_id].get("relationships", {}):
                    del data["characters"][char_id]["relationships"][other_char]
        
        self._save_relationships_data(data)
        return True
    
    def list_relationships(
        self,
        character_id: Optional[str] = None,
        rel_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        列出关系
        
        Args:
            character_id: 筛选某角色的关系
            rel_type: 筛选关系类型
            status: 筛选状态（active/inactive）
        
        Returns:
            关系列表
        """
        data = self._load_relationships_data()
        relationships = list(data.get("relationships", {}).values())
        
        # 过滤
        if character_id:
            relationships = [
                r for r in relationships
                if r["character_a"] == character_id or r["character_b"] == character_id
            ]
        
        if rel_type:
            relationships = [r for r in relationships if r["type"] == rel_type]
        
        if status:
            relationships = [r for r in relationships if r.get("status") == status]
        
        return deepcopy(relationships)
    
    def get_character_relationships(self, character_id: str) -> Dict[str, Dict[str, Any]]:
        """获取某角色的所有关系"""
        relationships = self.list_relationships(character_id=character_id)
        result = {}
        
        for rel in relationships:
            other_char = rel["character_b"] if rel["character_a"] == character_id else rel["character_a"]
            current_view_type = rel["type"] if rel["character_a"] == character_id else (rel.get("reverse_type") or rel["type"])
            result[other_char] = {
                "relationship_id": rel["id"],
                "type": current_view_type,
                "metrics": rel.get("metrics", {}),
                "status": rel.get("status"),
                "last_updated": rel.get("last_updated"),
            }
        
        return result
    
    def get_relationship_history(self, character_a: str, character_b: str) -> List[Dict[str, Any]]:
        """获取关系演变历史"""
        relationship = self.get_relationship(character_a, character_b)
        if not relationship:
            return []
        return deepcopy(relationship.get("history", []))
    
    # ==================== 阵营管理 ====================
    
    def create_faction(
        self,
        name: str,
        faction_type: str,
        members: List[str],
        enemies: Optional[List[str]] = None,
        allies: Optional[List[str]] = None,
        hierarchy: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        创建阵营
        
        Args:
            name: 阵营名称
            faction_type: 阵营类型（正派/反派/中立）
            members: 成员列表
            enemies: 敌对阵营 ID 列表
            allies: 盟友阵营 ID 列表
            hierarchy: 层级结构（leader/elders/members）
        
        Returns:
            创建的阵营对象
        """
        data = self._load_relationships_data()
        
        faction_id = name.lower().replace(" ", "_")
        
        if "factions" not in data:
            data["factions"] = {}
        
        if faction_id in data["factions"]:
            raise ValueError(f"阵营 {faction_id} 已存在")
        
        faction = {
            "id": faction_id,
            "name": name,
            "type": faction_type,
            "members": members,
            "enemies": enemies or [],
            "allies": allies or [],
            "hierarchy": hierarchy or {},
            "created_at": 1,
        }
        
        data["factions"][faction_id] = faction
        self._save_relationships_data(data)
        return deepcopy(faction)
    
    def add_faction_member(
        self,
        faction_id: str,
        character_id: str,
        role: str = "member",
    ) -> Dict[str, Any]:
        """
        添加阵营成员
        
        Args:
            faction_id: 阵营 ID
            character_id: 角色 ID
            role: 角色（leader/elder/member）
        
        Returns:
            更新后的阵营对象
        """
        data = self._load_relationships_data()
        
        if faction_id not in data.get("factions", {}):
            raise ValueError(f"阵营 {faction_id} 不存在")
        
        faction = data["factions"][faction_id]
        
        # 添加到成员列表
        if character_id not in faction["members"]:
            faction["members"].append(character_id)
        
        # 更新层级
        if "hierarchy" not in faction:
            faction["hierarchy"] = {}
        
        if role == "leader":
            # 移除旧领袖
            old_leader = faction["hierarchy"].get("leader")
            if old_leader:
                print(f"[Info] Removing old leader: {old_leader}")
            faction["hierarchy"]["leader"] = character_id
        elif role == "elder":
            if "elders" not in faction["hierarchy"]:
                faction["hierarchy"]["elders"] = []
            if character_id not in faction["hierarchy"]["elders"]:
                faction["hierarchy"]["elders"].append(character_id)
        else:
            if "members" not in faction["hierarchy"]:
                faction["hierarchy"]["members"] = []
            if character_id not in faction["hierarchy"]["members"]:
                faction["hierarchy"]["members"].append(character_id)
        
        data["factions"][faction_id] = faction
        self._save_relationships_data(data)
        return deepcopy(faction)
    
    def get_faction(self, faction_id: str) -> Optional[Dict[str, Any]]:
        """获取阵营信息"""
        data = self._load_relationships_data()
        return deepcopy(data.get("factions", {}).get(faction_id))
    
    def list_factions(self) -> List[Dict[str, Any]]:
        """列出所有阵营"""
        data = self._load_relationships_data()
        return deepcopy(list(data.get("factions", {}).values()))
    
    def remove_faction_member(self, faction_id: str, character_id: str) -> Dict[str, Any]:
        """移除阵营成员"""
        data = self._load_relationships_data()
        
        if faction_id not in data.get("factions", {}):
            raise ValueError(f"阵营 {faction_id} 不存在")
        
        faction = data["factions"][faction_id]
        
        # 从成员列表移除
        if character_id in faction["members"]:
            faction["members"].remove(character_id)
        
        # 从层级移除
        hierarchy = faction.get("hierarchy", {})
        if hierarchy.get("leader") == character_id:
            del hierarchy["leader"]
        if "elders" in hierarchy and character_id in hierarchy["elders"]:
            hierarchy["elders"].remove(character_id)
        if "members" in hierarchy and character_id in hierarchy["members"]:
            hierarchy["members"].remove(character_id)
        
        data["factions"][faction_id] = faction
        self._save_relationships_data(data)
        return deepcopy(faction)
    
    # ==================== 关系网络分析 ====================
    
    def get_relationship_network(self) -> Dict[str, Any]:
        """获取完整的关系网络"""
        data = self._load_relationships_data()
        
        return {
            "characters": list(data.get("characters", {}).keys()),
            "relationships": list(data.get("relationships", {}).values()),
            "factions": list(data.get("factions", {}).values()),
            "stats": {
                "total_characters": len(data.get("characters", {})),
                "total_relationships": len(data.get("relationships", {})),
                "total_factions": len(data.get("factions", {})),
            }
        }
    
    def get_relationship_between(self, character_a: str, character_b: str) -> Optional[Dict[str, Any]]:
        """获取两个角色之间的关系（简化版）"""
        return self.get_relationship(character_a, character_b)
