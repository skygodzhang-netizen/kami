"""
Book-level volume planning for novel-writer v3.0 Phase 3.

全书卷规划：卷名、字数、主角卷初/卷末状态、主活动区域、卷级核心矛盾。
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
    from .event_planning import DEFAULT_EVENT_CONFIG, extract_json_from_llm, merge_event_config
    from .project_layout import ProjectLayout
except ImportError:
    from event_planning import DEFAULT_EVENT_CONFIG, extract_json_from_llm, merge_event_config
    from project_layout import ProjectLayout


VOLUME_META_FIELDS = (
    "volume",
    "title",
    "target_words",
    "protagonist_state_start",
    "protagonist_state_end",
    "main_location",
    "core_conflict",
    "estimated_chapters",
)

# 卷弧阶段标签（规则桩）
_VOLUME_PHASE_LABELS = [
    ("起", "立足与入局", "被动承压", "初显锋芒"),
    ("承", "扩张与争锋", "站稳脚跟", "树敌立威"),
    ("转", "危机与破局", "多方施压", "绝境反杀"),
    ("合", "收束与钩子", "卷内目标达成", "更大风暴酝酿"),
    ("续", "新地图开启", "跨界入局", "格局再升级"),
]


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    os.replace(temp_path, path)


class BookPlanner:
    def __init__(self, layout: ProjectLayout, config: Optional[Dict[str, Any]] = None):
        self.layout = layout
        self.config = merge_event_config(config)
        self._json_path = self.layout.book_volume_plan_json_path()
        self._md_path = self.layout.book_volume_plan_path()

    def has_book_plan(self) -> bool:
        return self._md_path.exists() or self._json_path.exists()

    def load_plan_json(self) -> Dict[str, Any]:
        if not self._json_path.exists():
            return {}
        with open(self._json_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def load_plan_markdown(self) -> str:
        if not self._md_path.exists():
            return ""
        return self._md_path.read_text(encoding="utf-8")

    def save_plan(self, markdown: str, plan_json: Dict[str, Any]) -> Dict[str, str]:
        self.layout.planning_dir.mkdir(parents=True, exist_ok=True)
        md_normalized = str(markdown or "").strip() + "\n"
        _atomic_write_text(self._md_path, md_normalized)
        _atomic_write_text(
            self._json_path,
            f"{json.dumps(plan_json, ensure_ascii=False, indent=2)}\n",
        )
        return {"markdown_path": str(self._md_path), "json_path": str(self._json_path)}

    def generate_rule_stub(
        self,
        *,
        target_words: int = 1_000_000,
        total_volumes: Optional[int] = None,
        book_title: str = "",
    ) -> Tuple[str, Dict[str, Any]]:
        """Rule-based 全书卷规划（无需 LLM）。"""
        total = int(total_volumes or self.config.get("total_volumes") or 5)
        cpv = self.config.get("chapters_per_volume")
        words_per_vol = max(1, int(target_words) // max(total, 1))
        volumes: List[Dict[str, Any]] = []
        chapter_cursor = 1

        for index in range(total):
            vol_num = index + 1
            phase = _VOLUME_PHASE_LABELS[index % len(_VOLUME_PHASE_LABELS)]
            label, arc_hint, state_start, state_end = phase
            if cpv:
                est_chapters = int(cpv)
            else:
                est_chapters = max(
                    int(self.config.get("event_chapters_min") or 3) * 3,
                    20,
                )
            vol_words = words_per_vol
            start_ch = chapter_cursor
            end_ch = chapter_cursor + est_chapters - 1
            chapter_cursor = end_ch + 1

            volumes.append(
                {
                    "volume": vol_num,
                    "title": f"第{vol_num}卷·{label}",
                    "target_words": vol_words,
                    "protagonist_state_start": state_start,
                    "protagonist_state_end": state_end,
                    "main_location": f"第{vol_num}卷主活动区域",
                    "core_conflict": f"第{vol_num}卷核心矛盾：{arc_hint}",
                    "estimated_chapters": est_chapters,
                    "chapter_range": {"start": start_ch, "end": end_ch},
                    "volume_hook": "卷末留钩衔接下一卷" if vol_num < total else "全书阶段性收束",
                }
            )

        plan_json = {
            "book_title": book_title,
            "total_volumes": total,
            "target_words": int(target_words),
            "source": "rule_stub",
            "volumes": volumes,
        }
        markdown = self._render_markdown(plan_json)
        return markdown, plan_json

    def merge_llm_response(
        self,
        llm_text: str,
        *,
        target_words: int,
        total_volumes: int,
        book_title: str = "",
        fallback: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        try:
            payload = extract_json_from_llm(llm_text)
        except (ValueError, json.JSONDecodeError):
            if fallback:
                return self._render_markdown(fallback), fallback
            raise

        volumes_raw = payload.get("volumes") or []
        if not volumes_raw and fallback:
            return self._render_markdown(fallback), fallback

        volumes: List[Dict[str, Any]] = []
        chapter_cursor = 1
        for index, raw in enumerate(volumes_raw):
            vol_num = int(raw.get("volume") or index + 1)
            est = int(
                raw.get("estimated_chapters")
                or raw.get("chapters")
                or self.config.get("chapters_per_volume")
                or 30
            )
            start = int(raw.get("chapter_range", {}).get("start") or chapter_cursor)
            if start < chapter_cursor:
                start = chapter_cursor
            end = int(raw.get("chapter_range", {}).get("end") or start + est - 1)
            chapter_cursor = end + 1
            volumes.append(
                {
                    "volume": vol_num,
                    "title": raw.get("title", f"第{vol_num}卷"),
                    "target_words": int(raw.get("target_words") or target_words // max(total_volumes, 1)),
                    "protagonist_state_start": raw.get("protagonist_state_start", ""),
                    "protagonist_state_end": raw.get("protagonist_state_end", ""),
                    "main_location": raw.get("main_location", raw.get("location", "")),
                    "core_conflict": raw.get("core_conflict", ""),
                    "estimated_chapters": est,
                    "chapter_range": {"start": start, "end": end},
                    "volume_hook": raw.get("volume_hook", raw.get("hook_to_next_volume", "")),
                }
            )

        plan_json = {
            "book_title": payload.get("book_title") or book_title,
            "total_volumes": int(payload.get("total_volumes") or len(volumes) or total_volumes),
            "target_words": int(payload.get("target_words") or target_words),
            "source": "llm",
            "book_core_conflict": payload.get("book_core_conflict", ""),
            "volumes": volumes,
        }
        return self._render_markdown(plan_json), plan_json

    def get_volume_meta(self, volume_num: int) -> Optional[Dict[str, Any]]:
        plan = self.load_plan_json()
        for vol in plan.get("volumes", []):
            if int(vol.get("volume", 0)) == int(volume_num):
                return vol
        return None

    def get_volume_chapter_range(self, volume_num: int) -> Optional[Tuple[int, int]]:
        meta = self.get_volume_meta(volume_num)
        if not meta:
            return None
        cr = meta.get("chapter_range") or {}
        start = self._to_int(cr.get("start"))
        end = self._to_int(cr.get("end"))
        if start is not None and end is not None:
            return start, end
        est = self._to_int(meta.get("estimated_chapters"))
        if est and start is not None:
            return start, start + est - 1
        return None

    def find_volume_for_chapter(self, chapter_num: int) -> Optional[int]:
        plan = self.load_plan_json()
        for vol in plan.get("volumes", []):
            cr = vol.get("chapter_range") or {}
            start = self._to_int(cr.get("start"))
            end = self._to_int(cr.get("end"))
            if start is not None and end is not None and start <= chapter_num <= end:
                return int(vol.get("volume", 0))
        return None

    def get_transition_checklist(self, from_volume: int, to_volume: int) -> List[str]:
        next_meta = self.get_volume_meta(to_volume)
        items = [
            f"确认第 {from_volume} 卷 volume_event_plan 内所有事件 status ≥ beats_ready",
            f"更新 volume_arc / planning/volume_{to_volume}/volume_outline.md",
            f"执行 plan_volume_events(volume_num={to_volume}, pipeline=True)",
            "按事件顺序 plan_event → chapter_beats → write_chapter",
        ]
        if next_meta:
            items.insert(
                1,
                f"下一卷：{next_meta.get('title')} — {next_meta.get('core_conflict', '')[:60]}",
            )
        return items

    def _render_markdown(self, plan_json: Dict[str, Any]) -> str:
        lines = [
            f"# 全书卷规划：{plan_json.get('book_title') or '未命名'}",
            "",
            f"- **总卷数**：{plan_json.get('total_volumes')}",
            f"- **目标总字数**：{plan_json.get('target_words')}",
            "",
            "## 分卷一览",
            "",
            "| 卷 | 卷名 | 字数 | 章数 | 章号区间 | 主区域 | 核心矛盾 |",
            "|:--:|------|-----:|-----:|:--------:|--------|----------|",
        ]
        for vol in plan_json.get("volumes", []):
            cr = vol.get("chapter_range") or {}
            start = cr.get("start", "?")
            end = cr.get("end", "?")
            lines.append(
                f"| {vol.get('volume')} | {vol.get('title')} | "
                f"{vol.get('target_words')} | {vol.get('estimated_chapters')} | "
                f"{start}–{end} | {vol.get('main_location')} | {vol.get('core_conflict', '')[:30]} |"
            )
        lines.extend(["", "## 分卷详情", ""])
        for vol in plan_json.get("volumes", []):
            cr = vol.get("chapter_range") or {}
            lines.extend(
                [
                    f"### 第{vol.get('volume')}卷：{vol.get('title')}",
                    f"- **目标字数**：{vol.get('target_words')}",
                    f"- **章号区间**：第{cr.get('start')}–{cr.get('end')}章",
                    f"- **主角卷初**：{vol.get('protagonist_state_start')}",
                    f"- **主角卷末**：{vol.get('protagonist_state_end')}",
                    f"- **主活动区域**：{vol.get('main_location')}",
                    f"- **卷级核心矛盾**：{vol.get('core_conflict')}",
                    f"- **卷末钩子**：{vol.get('volume_hook', '')}",
                    "",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
