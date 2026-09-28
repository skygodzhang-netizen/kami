"""
Plot Workshop - Auto-generates plot packages from reusable tropes
"""
from typing import Any, Dict, List, Optional


class PlotWorkshop:
    def __init__(self):
        self.trope_library = [
            {
                "id": "misunderstanding_reversal",
                "name": "误会反转",
                "keywords": ["误会", "解释", "真相", "错认", "怀疑"],
                "fit": "适合关系紧张、信息不对称、人物试探阶段",
                "beats": ["埋下误会", "冲突升级", "真相撕开一角", "代价显现", "留下余波"],
                "scenes": ["错位对话", "第三方误导", "当面对质", "半真半假地解释", "带伤收场"],
            },
            {
                "id": "resource_competition",
                "name": "资源争夺",
                "keywords": ["机缘", "资源", "争夺", "遗迹", "拍卖", "宝物"],
                "fit": "适合升级文、竞争关系、节奏加速阶段",
                "beats": ["目标出现", "各方入局", "暗手试探", "正面争夺", "更大麻烦降临"],
                "scenes": ["争宝前夜", "试探性结盟", "临场变卦", "强行截胡", "胜而未稳"],
            },
            {
                "id": "identity_exposure",
                "name": "身份暴露",
                "keywords": ["身份", "暴露", "卧底", "秘密", "伪装", "马甲"],
                "fit": "适合双线身份、阵营冲突、主角承压阶段",
                "beats": ["异常迹象", "有人起疑", "证据逼近", "局部暴露", "危机外扩"],
                "scenes": ["熟人试探", "细节穿帮", "紧急补救", "被迫承认一半", "尾声留钩"],
            },
            {
                "id": "faction_pressure",
                "name": "阵营施压",
                "keywords": ["阵营", "宗门", "立场", "派系", "忠诚", "站队"],
                "fit": "适合组织冲突、师门关系、权力拉扯阶段",
                "beats": ["内部施压", "外部诱逼", "人物摇摆", "被迫表态", "后续报复或奖赏"],
                "scenes": ["长辈谈话", "同伴劝说", "利益交换", "公开站队", "私下补刀"],
            },
            {
                "id": "emotional_breakthrough",
                "name": "关系破冰",
                "keywords": ["靠近", "信任", "心结", "救助", "亏欠", "和解"],
                "fit": "适合情感线推进、角色升温、关系回暖阶段",
                "beats": ["旧伤再提", "被迫合作", "细节破防", "关系松动", "留下未说透的钩子"],
                "scenes": ["嘴硬帮忙", "共处封闭空间", "伤口处理", "一句话说重", "沉默后的靠近"],
            },
            {
                "id": "strong_enemy_descends",
                "name": "强敌压境",
                "keywords": ["强敌", "追杀", "危机", "压境", "悬赏", "围杀"],
                "fit": "适合中后段推进、爽点制造、章节钩子增强阶段",
                "beats": ["危险逼近", "试探交锋", "战力落差显露", "险中求活", "留下更大敌意"],
                "scenes": ["突然封锁", "越级交手", "临场爆发", "断后撤退", "敌人记住主角"],
            },
        ]

    def generate_plot(self, progress_node, character_status, **kwargs):
        workshop_context = self._build_context_text(progress_node, character_status, **kwargs)
        selected_trope = self._select_trope(workshop_context, kwargs.get("trope_hint"))
        title = kwargs.get("title") or f"剧情工坊方案：{selected_trope['name']}"

        plot_package = {
            "title": title,
            "selected_trope": {
                "id": selected_trope["id"],
                "name": selected_trope["name"],
                "fit": selected_trope["fit"],
            },
            "plot_outline": {
                "setup": self._build_setup(progress_node, kwargs),
                "conflict": self._build_conflict(selected_trope, kwargs),
                "turn": self._build_turn(selected_trope, kwargs),
                "payoff": self._build_payoff(selected_trope, kwargs),
                "hook": self._build_hook(selected_trope, kwargs),
            },
            "scene_beats": self._build_scene_beats(selected_trope, kwargs),
            "constraints": self._build_constraints(kwargs),
            "context_summary": workshop_context[:600],
        }
        return plot_package

    def _build_context_text(self, progress_node: Any, character_status: Any, **kwargs) -> str:
        parts = [
            str(progress_node or ""),
            str(character_status or ""),
            str(kwargs.get("world_hooks") or ""),
            str(kwargs.get("relationship_context") or ""),
            str(kwargs.get("faction_context") or ""),
            str(kwargs.get("core_pleasure") or ""),
            str(kwargs.get("genre") or ""),
            str(kwargs.get("goal") or ""),
        ]
        return "\n".join(part for part in parts if part).strip()

    def _select_trope(self, context_text: str, trope_hint: str | None) -> Dict[str, Any]:
        if trope_hint:
            hinted = trope_hint.strip().lower()
            for trope in self.trope_library:
                if hinted in {trope["id"], trope["name"].lower()}:
                    return trope

        lowered = context_text.lower()
        best_trope = self.trope_library[0]
        best_score = -1
        for trope in self.trope_library:
            score = sum(1 for keyword in trope["keywords"] if keyword.lower() in lowered)
            if score > best_score:
                best_score = score
                best_trope = trope
        return best_trope

    def _build_setup(self, progress_node: Any, kwargs: Dict[str, Any]) -> str:
        base = str(progress_node or kwargs.get("goal") or "当前剧情进入新冲突前夜").strip()
        return f"以“{base[:80] or '当前局面未稳'}”作为起点，先让角色带着明确诉求入场。"

    def _build_conflict(self, trope: Dict[str, Any], kwargs: Dict[str, Any]) -> str:
        target = kwargs.get("target_conflict") or trope["name"]
        return f"本次主冲突围绕“{target}”展开，优先制造信息差、立场差或利益差。"

    def _build_turn(self, trope: Dict[str, Any], kwargs: Dict[str, Any]) -> str:
        return f"中段转折采用“{trope['beats'][2]}”，让角色判断失误或被迫临场改口。"

    def _build_payoff(self, trope: Dict[str, Any], kwargs: Dict[str, Any]) -> str:
        payoff = kwargs.get("desired_payoff") or trope["beats"][3]
        return f"本章兑现点放在“{payoff}”，让读者获得阶段性满足，但不收死后续空间。"

    def _build_hook(self, trope: Dict[str, Any], kwargs: Dict[str, Any]) -> str:
        chapter_goal = kwargs.get("chapter_goal") or "把麻烦升级到下一章"
        return f"结尾采用“{trope['beats'][-1]}”式钩子，目的：{chapter_goal}。"

    def _build_scene_beats(self, trope: Dict[str, Any], kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
        beats = []
        for index, scene_name in enumerate(trope["scenes"], start=1):
            beats.append(
                {
                    "order": index,
                    "scene": scene_name,
                    "purpose": trope["beats"][min(index - 1, len(trope["beats"]) - 1)],
                }
            )
        return beats

    def _build_constraints(self, kwargs: Dict[str, Any]) -> List[str]:
        constraints = [
            "只复用桥段骨架，不照搬具体作品设定、名词和事件排列。",
            "桥段必须服务当前章节节点，不能为了工坊桥段反向篡改主线。",
            "优先保留人物关系温差和情绪递进，不要只剩套路动作。",
        ]
        if kwargs.get("genre"):
            constraints.append(f"题材适配：当前按“{kwargs['genre']}”口径调整桥段表达。")
        if kwargs.get("core_pleasure"):
            constraints.append(f"爽点锚定：优先满足“{kwargs['core_pleasure']}”。")
        return constraints

    def get_trope_by_id(self, trope_id: str) -> Optional[Dict[str, Any]]:
        target = str(trope_id).strip().lower()
        for trope in self.trope_library:
            if trope["id"] == target or trope["name"].lower() == target:
                return trope
        return None

    def generate_volume_workshop(
        self,
        volume_num: int,
        *,
        volume_arc: str = "",
        world_hooks: str = "",
        event_count: int = 3,
        event_chapters_min: int = 3,
        event_chapters_max: int = 15,
        genre: Optional[str] = None,
        core_pleasure: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rule-based volume event cards (scope=volume, no LLM)."""
        context = self._build_context_text(volume_arc, world_hooks, genre=genre, core_pleasure=core_pleasure)
        templates = [
            (["misunderstanding_reversal", "faction_pressure"], "入局", "卷初立足"),
            (["resource_competition", "strong_enemy_descends"], "争锋", "中段加压"),
            (["identity_exposure", "emotional_breakthrough"], "破局", "卷末收束"),
        ]
        mid = max(event_chapters_min, min(event_chapters_max, (event_chapters_min + event_chapters_max) // 2))
        chapter_hints = [event_chapters_min + 1, mid + 1, event_chapters_max - 2]
        while len(chapter_hints) < event_count:
            chapter_hints.append(mid)

        cards: List[Dict[str, Any]] = []
        for index in range(event_count):
            tropes, suffix, phase = templates[index % len(templates)]
            trope_names = [self.get_trope_by_id(tid)["name"] for tid in tropes if self.get_trope_by_id(tid)]
            cards.append(
                {
                    "event_id": f"e{index + 1:02d}",
                    "title": f"第{volume_num}卷·{suffix}",
                    "trope_ids": list(tropes),
                    "trope_rationale": f"{phase}阶段采用「{'+'.join(trope_names)}」组合，服务卷弧递进。",
                    "estimated_chapters": int(chapter_hints[index]),
                    "protagonist_state_start": f"{phase}起点：处境与卷弧节点对齐",
                    "protagonist_state_end": f"{phase}终点：留下面向下一事件的张力",
                    "location": "卷内主活动区域",
                    "hook_to_next": "麻烦升级或信息翻面" if index < event_count - 1 else "卷末衔接下一卷",
                    "emotion_arc": "紧张→对抗→阶段性释放",
                }
            )

        return {
            "scope": "volume",
            "volume": int(volume_num),
            "source": "rule",
            "context_summary": context[:600],
            "event_cards": cards,
            "volume_emotion_line": "低开铺垫→连续加压→卷末高潮与钩子",
            "constraints": self._build_volume_constraints(genre, core_pleasure),
        }

    def generate_event_workshop(
        self,
        event_card: Dict[str, Any],
        *,
        volume_workshop: Optional[Dict[str, Any]] = None,
        world_hooks: str = "",
        genre: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rule-based scene beats for one event (scope=event)."""
        trope_ids = event_card.get("trope_ids") or []
        primary = self.get_trope_by_id(trope_ids[0]) if trope_ids else self.trope_library[0]
        secondary = self.get_trope_by_id(trope_ids[1]) if len(trope_ids) > 1 else None

        scene_beats: List[Dict[str, Any]] = []
        for index, scene_name in enumerate(primary["scenes"], start=1):
            scene_beats.append(
                {
                    "order": index,
                    "scene": scene_name,
                    "purpose": primary["beats"][min(index - 1, len(primary["beats"]) - 1)],
                    "trope": primary["id"],
                }
            )
        if secondary:
            scene_beats.append(
                {
                    "order": len(scene_beats) + 1,
                    "scene": secondary["scenes"][0],
                    "purpose": f"叠加「{secondary['name']}」余波",
                    "trope": secondary["id"],
                }
            )

        est = int(event_card.get("estimated_chapters") or 5)
        hints = []
        roles = ["立局", "加压", "转折", "兑现", "篇末钩"]
        emotions = ["紧张", "愤怒", "震惊", "释放", "期待"]
        for offset in range(1, est + 1):
            role_idx = min(offset - 1, len(roles) - 1)
            hints.append(
                {
                    "chapter_offset": offset,
                    "focus": roles[role_idx],
                    "emotion": emotions[role_idx],
                }
            )

        vol_constraints = (volume_workshop or {}).get("constraints") or []
        return {
            "scope": "event",
            "event_id": event_card.get("event_id"),
            "title": event_card.get("title"),
            "selected_tropes": [
                {"id": t["id"], "name": t["name"]}
                for tid in trope_ids
                if (t := self.get_trope_by_id(tid))
            ],
            "scene_beats": scene_beats,
            "constraints": self._build_constraints({"genre": genre})
            + [f"继承卷级约束：{c}" for c in vol_constraints[:3]],
            "chapter_allocation_hints": hints,
            "context_summary": str(world_hooks or "")[:400],
        }

    def _build_volume_constraints(
        self,
        genre: Optional[str],
        core_pleasure: Optional[str],
    ) -> List[str]:
        items = [
            "事件卡片只提供桥段组合骨架，不替代卷情绪弧。",
            "每事件须有独立篇末钩子，禁止断档。",
            "章数为预估，可在事件级推演时微调。",
        ]
        if genre:
            items.append(f"题材：{genre}")
        if core_pleasure:
            items.append(f"爽点锚定：{core_pleasure}")
        return items
