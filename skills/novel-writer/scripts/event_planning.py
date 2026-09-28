"""
Event / 篇 planning layer for novel-writer v3.0.

Phase 1: rule-based volume event cards + event outlines (no LLM required).
"""
from __future__ import annotations

import json
import re
import tempfile
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from .project_layout import ProjectLayout
except ImportError:
    from project_layout import ProjectLayout


EVENT_REQUIRED_FIELDS = (
    "event_id",
    "volume",
    "title",
    "trope_ids",
    "estimated_chapters",
    "actual_chapters",
    "protagonist_state_start",
    "protagonist_state_end",
    "location",
    "hook_to_next",
    "status",
)

DEFAULT_EVENT_CONFIG = {
    "total_volumes": 5,
    "chapters_per_volume": None,
    "event_chapters_min": 3,
    "event_chapters_max": 15,
    "events_per_volume_default": 3,
    "plot_workshop_per_chapter_enabled": False,
    "plot_engine_per_chapter_enabled": False,
    "event_planning_enabled": True,
    "require_book_volume_plan_at_pre_init": False,
}

# Trope combos for rule-based volume event cards (Phase 1 stub)
_VOLUME_EVENT_TEMPLATES = [
    {
        "title_suffix": "入局",
        "trope_ids": ["misunderstanding_reversal", "faction_pressure"],
        "location": "主活动区域入口",
        "state_start": "卷初：处境被动、信息不足",
        "state_end": "站稳脚跟，但得罪局部势力",
        "hook": "更大麻烦找上门",
    },
    {
        "title_suffix": "争锋",
        "trope_ids": ["resource_competition", "strong_enemy_descends"],
        "location": "冲突核心区",
        "state_start": "被迫应战、资源紧缺",
        "state_end": "险胜一局，暴露底牌一角",
        "hook": "旧敌未灭，新变量出现",
    },
    {
        "title_suffix": "破局",
        "trope_ids": ["identity_exposure", "emotional_breakthrough"],
        "location": "卷末高潮场景",
        "state_start": "多方施压、身份濒临暴露",
        "state_end": "卷内阶段性目标达成，留下卷间钩子",
        "hook": "通往下一卷的核心矛盾浮出水面",
    },
]


def merge_event_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged = deepcopy(DEFAULT_EVENT_CONFIG)
    if config:
        for key in DEFAULT_EVENT_CONFIG:
            if key in config and config[key] is not None:
                merged[key] = config[key]
    return merged


def validate_event(event: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for field in EVENT_REQUIRED_FIELDS:
        if field not in event:
            errors.append(f"事件缺少字段：{field}")
    if event.get("estimated_chapters") is not None:
        try:
            est = int(event["estimated_chapters"])
            if est < 1:
                errors.append("estimated_chapters 须 >= 1")
        except (TypeError, ValueError):
            errors.append("estimated_chapters 须为整数")
    return errors


def extract_json_from_llm(text: str) -> Dict[str, Any]:
    """Extract first JSON object from LLM response."""
    if not text or not str(text).strip():
        raise ValueError("LLM 输出为空")
    candidate = str(text).strip()
    fenced = re.search(r"```json\s*(.*?)\s*```", candidate, flags=re.S | re.I)
    if fenced:
        candidate = fenced.group(1).strip()
    else:
        brace = re.search(r"\{.*\}", candidate, flags=re.S)
        if brace:
            candidate = brace.group(0)
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("JSON 须为对象")
    return parsed


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    os.replace(temp_path, path)


class EventPlanner:
    def __init__(self, layout: ProjectLayout, config: Optional[Dict[str, Any]] = None):
        self.layout = layout
        self.event_config = merge_event_config(config)

    def uses_event_planning(self, volume_num: Optional[int] = None) -> bool:
        if not self.event_config.get("event_planning_enabled", True):
            return False
        if volume_num is not None:
            return self.layout.volume_event_plan_path(volume_num).exists()
        for plan_path in sorted(self.layout.planning_dir.glob("volume_*/volume_event_plan.json")):
            if plan_path.exists():
                return True
        return False

    def is_legacy_mode(self, volume_num: Optional[int] = None) -> bool:
        return not self.uses_event_planning(volume_num)

    def load_volume_event_plan(self, volume_num: int) -> Dict[str, Any]:
        path = self.layout.volume_event_plan_path(volume_num)
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def save_volume_event_plan(self, plan: Dict[str, Any]) -> Path:
        volume_num = int(plan["volume"])
        self.layout.ensure_volume_planning_dirs(volume_num)
        path = self.layout.volume_event_plan_path(volume_num)
        _atomic_write_text(path, f"{json.dumps(plan, ensure_ascii=False, indent=2)}\n")
        return path

    def plan_volume_events(
        self,
        volume_num: int,
        *,
        volume_title: str = "",
        event_count: Optional[int] = None,
        volume_arc_text: str = "",
    ) -> Dict[str, Any]:
        """Rule-based volume event card list (Phase 1 — no LLM)."""
        cfg = self.event_config
        count = int(event_count or cfg.get("events_per_volume_default") or 3)
        ch_min = int(cfg.get("event_chapters_min") or 3)
        ch_max = int(cfg.get("event_chapters_max") or 15)
        cap = cfg.get("chapters_per_volume")
        per_event = self._distribute_chapters(count, ch_min, ch_max, cap)

        base_chapter = self._volume_start_chapter(volume_num)
        events: List[Dict[str, Any]] = []
        cursor = base_chapter

        for index in range(count):
            template = _VOLUME_EVENT_TEMPLATES[index % len(_VOLUME_EVENT_TEMPLATES)]
            event_id = f"e{index + 1:02d}"
            est = per_event[index]
            title = f"第{volume_num}卷·{template['title_suffix']}"
            if volume_title:
                title = f"{volume_title}·{template['title_suffix']}"

            events.append(
                {
                    "event_id": event_id,
                    "volume": volume_num,
                    "title": title,
                    "trope_ids": list(template["trope_ids"]),
                    "estimated_chapters": est,
                    "actual_chapters": 0,
                    "start_chapter": cursor,
                    "protagonist_state_start": template["state_start"],
                    "protagonist_state_end": template["state_end"],
                    "location": template["location"],
                    "hook_to_next": template["hook"] if index < count - 1 else "卷末衔接下一卷",
                    "status": "planned",
                }
            )
            cursor += est

        transitions = []
        for idx in range(len(events) - 1):
            left = events[idx]
            right = events[idx + 1]
            transitions.append(
                {
                    "from": left["event_id"],
                    "to": right["event_id"],
                    "bridge": left.get("hook_to_next", ""),
                }
            )

        plan = {
            "volume": volume_num,
            "title": volume_title or f"第{volume_num}卷",
            "source": "rule_stub",
            "volume_arc_excerpt": (volume_arc_text or "")[:500],
            "events": events,
            "transitions": transitions,
            "chapter_range": {
                "start": base_chapter,
                "end": cursor - 1,
            },
        }
        path = self.save_volume_event_plan(plan)
        return {"plan": plan, "path": str(path), "event_count": len(events)}

    def build_plan_from_volume_workshop(
        self,
        volume_num: int,
        workshop: Dict[str, Any],
        *,
        volume_title: str = "",
        volume_arc_text: str = "",
        source: str = "workshop",
    ) -> Dict[str, Any]:
        """Convert volume workshop cards into volume_event_plan.json."""
        cards = workshop.get("event_cards") or []
        base_chapter = self._volume_start_chapter(volume_num)
        cursor = base_chapter
        events: List[Dict[str, Any]] = []

        for card in cards:
            est = int(card.get("estimated_chapters") or card.get("estimated_chapters_hint") or 5)
            event_id = str(card.get("event_id") or f"e{len(events) + 1:02d}")
            events.append(
                {
                    "event_id": event_id,
                    "volume": volume_num,
                    "title": card.get("title") or f"第{volume_num}卷事件",
                    "trope_ids": list(card.get("trope_ids") or []),
                    "estimated_chapters": est,
                    "actual_chapters": 0,
                    "start_chapter": cursor,
                    "protagonist_state_start": card.get("protagonist_state_start", ""),
                    "protagonist_state_end": card.get("protagonist_state_end", ""),
                    "location": card.get("location", card.get("location_hint", "")),
                    "hook_to_next": card.get("hook_to_next", ""),
                    "status": "planned",
                }
            )
            cursor += est

        transitions = []
        for idx in range(len(events) - 1):
            transitions.append(
                {
                    "from": events[idx]["event_id"],
                    "to": events[idx + 1]["event_id"],
                    "bridge": events[idx].get("hook_to_next", ""),
                }
            )

        plan = {
            "volume": volume_num,
            "title": volume_title or f"第{volume_num}卷",
            "source": source,
            "volume_emotion_line": workshop.get("volume_emotion_line", ""),
            "volume_arc_excerpt": (volume_arc_text or "")[:500],
            "events": events,
            "transitions": transitions,
            "chapter_range": {"start": base_chapter, "end": cursor - 1},
        }
        path = self.save_volume_event_plan(plan)
        return {"plan": plan, "path": str(path), "event_count": len(events)}

    def merge_volume_engine_response(
        self,
        volume_num: int,
        engine_text: str,
        *,
        fallback_workshop: Optional[Dict[str, Any]] = None,
        volume_arc_text: str = "",
    ) -> Dict[str, Any]:
        """Parse plot_engine scope=volume output and save volume_event_plan."""
        try:
            payload = extract_json_from_llm(engine_text)
        except (ValueError, json.JSONDecodeError):
            if fallback_workshop:
                return self.build_plan_from_volume_workshop(
                    volume_num,
                    fallback_workshop,
                    volume_arc_text=volume_arc_text,
                    source="workshop_fallback",
                )
            raise

        events_raw = payload.get("events") or payload.get("event_cards") or []
        if not events_raw and fallback_workshop:
            return self.build_plan_from_volume_workshop(
                volume_num,
                fallback_workshop,
                volume_title=str(payload.get("title") or ""),
                volume_arc_text=volume_arc_text,
                source="workshop_fallback",
            )

        base_chapter = self._volume_start_chapter(volume_num)
        cursor = base_chapter
        events: List[Dict[str, Any]] = []
        for index, raw in enumerate(events_raw):
            est = int(raw.get("estimated_chapters") or 5)
            start = int(raw.get("start_chapter") or cursor)
            if start < cursor:
                start = cursor
            events.append(
                {
                    "event_id": str(raw.get("event_id") or f"e{index + 1:02d}"),
                    "volume": volume_num,
                    "title": raw.get("title", ""),
                    "trope_ids": list(raw.get("trope_ids") or []),
                    "estimated_chapters": est,
                    "actual_chapters": int(raw.get("actual_chapters") or 0),
                    "start_chapter": start,
                    "protagonist_state_start": raw.get("protagonist_state_start", ""),
                    "protagonist_state_end": raw.get("protagonist_state_end", ""),
                    "location": raw.get("location", ""),
                    "hook_to_next": raw.get("hook_to_next", ""),
                    "status": raw.get("status", "planned"),
                }
            )
            cursor = start + est

        transitions = payload.get("transitions") or []
        if not transitions:
            for idx in range(len(events) - 1):
                transitions.append(
                    {
                        "from": events[idx]["event_id"],
                        "to": events[idx + 1]["event_id"],
                        "bridge": events[idx].get("hook_to_next", ""),
                    }
                )

        plan = {
            "volume": volume_num,
            "title": payload.get("title") or f"第{volume_num}卷",
            "source": "plot_engine_volume",
            "volume_emotion_line": payload.get("volume_emotion_line", ""),
            "volume_arc_excerpt": (volume_arc_text or "")[:500],
            "events": events,
            "transitions": transitions,
            "chapter_range": {
                "start": events[0]["start_chapter"] if events else base_chapter,
                "end": cursor - 1 if events else base_chapter,
            },
        }
        path = self.save_volume_event_plan(plan)
        return {
            "plan": plan,
            "path": str(path),
            "event_count": len(events),
            "engine_excerpt": engine_text[:2000],
        }

    def save_event_outline_from_engine(
        self,
        volume_num: int,
        event_id: str,
        outline_text: str,
    ) -> Dict[str, Any]:
        plan = self.load_volume_event_plan(volume_num)
        event = self.get_event(plan, event_id)
        if not event:
            raise ValueError(f"事件 {event_id} 不在卷 {volume_num} 规划内")

        path = self.layout.event_outline_path(volume_num, event_id)
        normalized = str(outline_text or "").strip()
        if not normalized.startswith("---"):
            start, end = self.event_chapter_range(event)
            normalized = (
                f"---\nevent_id: {event_id}\nvolume: {volume_num}\n"
                f"title: {event.get('title')}\nstatus: outlined\n---\n\n{normalized}"
            )
        _atomic_write_text(path, normalized + "\n")

        for item in plan.get("events", []):
            if item.get("event_id") == event_id:
                item["status"] = "outlined"
        self.save_volume_event_plan(plan)
        return {
            "event": event,
            "outline": normalized,
            "path": str(path),
            "chapter_range": self.event_chapter_range(event),
        }

    def plan_event(
        self,
        volume_num: int,
        event_id: str,
        *,
        extra_notes: str = "",
    ) -> Dict[str, Any]:
        """Expand a single event into event_outline.md (Phase 1 — template, no LLM)."""
        plan = self.load_volume_event_plan(volume_num)
        if not plan:
            raise FileNotFoundError(f"缺少卷级事件规划：volume_{volume_num}/volume_event_plan.json")

        event = self.get_event(plan, event_id)
        if not event:
            raise ValueError(f"事件 {event_id} 不在卷 {volume_num} 规划内")

        outline = self._render_event_outline(event, plan, extra_notes=extra_notes)
        path = self.layout.event_outline_path(volume_num, event_id)
        _atomic_write_text(path, outline)

        for item in plan.get("events", []):
            if item.get("event_id") == event_id:
                item["status"] = "outlined"
        self.save_volume_event_plan(plan)

        return {
            "event": event,
            "outline": outline,
            "path": str(path),
            "chapter_range": self.event_chapter_range(event),
        }

    def get_event(self, plan: Dict[str, Any], event_id: str) -> Optional[Dict[str, Any]]:
        target = str(event_id).strip().lower()
        for event in plan.get("events", []):
            if str(event.get("event_id", "")).lower() == target:
                return event
        return None

    def find_event_for_chapter(self, volume_num: int, chapter_num: int) -> Optional[Dict[str, Any]]:
        plan = self.load_volume_event_plan(volume_num)
        if not plan:
            return None
        for event in plan.get("events", []):
            start, end = self.event_chapter_range(event)
            if start <= chapter_num <= end:
                return event
        return None

    def event_chapter_range(self, event: Dict[str, Any]) -> Tuple[int, int]:
        start = int(event.get("start_chapter") or 1)
        est = int(event.get("estimated_chapters") or 1)
        actual = int(event.get("actual_chapters") or 0)
        span = actual if actual > 0 else est
        return start, start + max(span, 1) - 1

    def validate_chapter_beats_gate(
        self,
        volume_num: int,
        event_id: Optional[str],
        *,
        allow_legacy: bool = True,
    ) -> Dict[str, Any]:
        blockers: List[str] = []
        if self.is_legacy_mode(volume_num):
            if allow_legacy:
                return {"ready": True, "blockers": [], "legacy": True}
            blockers.append("项目未启用事件规划层")
            return {"ready": False, "blockers": blockers, "legacy": True}

        if not event_id:
            blockers.append(
                "chapter_beats 禁止在未指定 event_id 时为整卷批量生成。"
                "请先 plan_volume_events → plan_event，再对单事件生成章节拍。"
            )
            return {"ready": False, "blockers": blockers, "legacy": False}

        plan = self.load_volume_event_plan(volume_num)
        event = self.get_event(plan, event_id) if plan else None
        if not event:
            blockers.append(f"事件 {event_id} 不存在于 volume_{volume_num} 规划")
            return {"ready": False, "blockers": blockers, "legacy": False}

        outline_path = self.layout.event_outline_path(volume_num, event_id)
        if not outline_path.exists():
            blockers.append(
                f"缺少事件纲：{outline_path.relative_to(self.layout.run_dir)}。"
                "请先执行 plan_event。"
            )

        return {
            "ready": not blockers,
            "blockers": blockers,
            "legacy": False,
            "event": event,
            "event_outline_path": str(outline_path),
        }

    def validate_event_preflight(
        self,
        volume_num: int,
        chapter_num: int,
    ) -> Dict[str, Any]:
        blockers: List[str] = []
        warnings: List[str] = []

        if self.is_legacy_mode(volume_num):
            return {"ready": True, "blockers": [], "warnings": [], "legacy": True}

        plan_path = self.layout.volume_event_plan_path(volume_num)
        if not plan_path.exists():
            blockers.append(f"缺少卷级事件规划：{plan_path.relative_to(self.layout.run_dir)}")
            return {"ready": False, "blockers": blockers, "warnings": warnings, "legacy": False}

        event = self.find_event_for_chapter(volume_num, chapter_num)
        if not event:
            blockers.append(f"第 {chapter_num} 章未映射到 volume_{volume_num} 内任何事件")
            return {"ready": False, "blockers": blockers, "warnings": warnings, "legacy": False}

        event_id = event.get("event_id")
        outline_path = self.layout.event_outline_path(volume_num, str(event_id))
        if not outline_path.exists():
            blockers.append(f"第 {chapter_num} 章所属事件 {event_id} 缺少 event_outline")

        if event.get("status") == "planned":
            warnings.append(f"事件 {event_id} 仍为 planned，建议先 plan_event")

        return {
            "ready": not blockers,
            "blockers": blockers,
            "warnings": warnings,
            "legacy": False,
            "event": event,
            "event_id": event_id,
            "volume_event_plan_path": str(plan_path),
            "event_outline_path": str(outline_path) if outline_path.exists() else None,
        }

    def mark_event_beats_ready(self, volume_num: int, event_id: str, actual_chapters: int) -> None:
        plan = self.load_volume_event_plan(volume_num)
        for item in plan.get("events", []):
            if item.get("event_id") == event_id:
                item["status"] = "beats_ready"
                item["actual_chapters"] = int(actual_chapters)
        self.save_volume_event_plan(plan)

    def _volume_start_chapter(self, volume_num: int) -> int:
        try:
            from book_planning import BookPlanner
        except ImportError:
            from .book_planning import BookPlanner
        book_range = BookPlanner(self.layout, self.event_config).get_volume_chapter_range(volume_num)
        if book_range:
            return book_range[0]
        if volume_num <= 1:
            return 1
        start = 1
        for vol in range(1, volume_num):
            prev = self.load_volume_event_plan(vol)
            if prev and prev.get("chapter_range"):
                start = int(prev["chapter_range"]["end"]) + 1
            else:
                cap = self.event_config.get("chapters_per_volume")
                if cap:
                    start += int(cap)
        return start

    def _distribute_chapters(
        self,
        count: int,
        ch_min: int,
        ch_max: int,
        volume_cap: Optional[int],
    ) -> List[int]:
        if count < 1:
            return [ch_min]
        if volume_cap:
            total = int(volume_cap)
            base = max(ch_min, total // count)
            base = min(base, ch_max)
            parts = [base] * count
            remainder = total - base * count
            for idx in range(remainder):
                if parts[idx] < ch_max:
                    parts[idx] += 1
            return parts
        # Default: middle of range, slight arc (first shorter, middle longer)
        mid = max(ch_min, min(ch_max, (ch_min + ch_max) // 2))
        if count == 1:
            return [mid]
        if count == 2:
            return [ch_min + 1, mid + 1]
        return [ch_min + 1, mid + 2, ch_max - 2][:count] + [mid] * max(0, count - 3)

    def _render_event_outline(
        self,
        event: Dict[str, Any],
        plan: Dict[str, Any],
        *,
        extra_notes: str = "",
    ) -> str:
        start, end = self.event_chapter_range(event)
        tropes = ", ".join(event.get("trope_ids") or [])
        lines = [
            "---",
            f"event_id: {event.get('event_id')}",
            f"volume: {event.get('volume')}",
            f"title: {event.get('title')}",
            f"estimated_chapters: {event.get('estimated_chapters')}",
            f"chapter_range: {start}-{end}",
            f"status: outlined",
            "---",
            "",
            f"# {event.get('title')}",
            "",
            "## 事件目标",
            f"- 主角从「{event.get('protagonist_state_start')}」推进到「{event.get('protagonist_state_end')}」",
            f"- 主活动区域：{event.get('location')}",
            f"- 桥段组合：{tropes}",
            "",
            "## 场景与人物",
            "- 核心冲突：信息差 + 立场差驱动的阶段性博弈",
            "- 人物：主角、对立面、至少一名贯穿配角",
            "",
            "## 桥段节奏（篇内）",
            "1. 入局 — 明确诉求与当下困境",
            "2. 加压 — 误会/资源/阵营至少一项升级",
            "3. 转折 — 局部真相或底牌露头",
            "4. 兑现 — 阶段性爽点或情绪释放",
            "5. 篇末钩子 — " + str(event.get("hook_to_next") or ""),
            "",
            "## 章数分配建议",
            f"- 本事件覆盖第 {start}–{end} 章（共 {event.get('estimated_chapters')} 章）",
            "- 建议：开篇 1 章立局，中段铺压，末 1–2 章收束并留钩",
            "",
            "## 与卷内衔接",
        ]
        for transition in plan.get("transitions", []):
            if transition.get("from") == event.get("event_id"):
                lines.append(
                    f"- 通往 {transition.get('to')}：{transition.get('bridge', '')}"
                )
        if extra_notes.strip():
            lines.extend(["", "## 备注", extra_notes.strip()])
        return "\n".join(lines) + "\n"
