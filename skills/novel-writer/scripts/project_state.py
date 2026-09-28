"""
Project State Machine — 小说项目数据状态机

与 ConfigManager 共用目录布局与 workflow schema，避免双轨状态。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from .config_manager import ConfigManager
    from .project_layout import ProjectLayout
except ImportError:
    from config_manager import ConfigManager
    from project_layout import ProjectLayout


class ChapterDiff:
    """从终稿文本提取状态变化（题材无关的通用规则）"""

    CULTIVATION_PATTERNS = [
        r"(?:突破|晋升|踏入|达到|晋级)(?:了)?\s*([\u4e00-\u9fff]{2,12})(?:\s*(初期|中期|后期|巅峰|一层|二层|三层))?",
        r"(?:修为|境界|实力|等级)\s*(?:提升|突破|达到|涨至)\s*(?:了)?\s*([\u4e00-\u9fff]{2,12})",
    ]

    ITEM_ACQUIRE_PATTERNS = [
        r"(?:获得|得到|拿到|收取|入手)\s*(?:了)?\s*[「『\"'](.+?)[」』\"']",
        r"【获得[^】]*?([\u4e00-\u9fff]{2,10})[^】]*】",
    ]

    # Quoted utterances are dialogue, not character identities.
    # Keep only an explicit named-speaker pattern; project canon remains authoritative.
    DIALOGUE_NAME_PATTERNS = [
        r"(?:^|[。！？\n])\s*([\u4e00-\u9fff]{2,4})(?:说|道|问|答|喊|叫)[：:]",
    ]

    @classmethod
    def detect(cls, chapter_text: str, existing_state: Dict[str, Any]) -> Dict[str, Any]:
        diff = {
            "cultivation_changes": cls._detect_cultivation(chapter_text),
            "items_acquired": cls._detect_items(chapter_text),
            "characters_appeared": cls._detect_characters(chapter_text, existing_state),
            "key_events": cls._extract_key_events(chapter_text),
        }
        diff["has_changes"] = any(
            [
                diff["cultivation_changes"],
                diff["items_acquired"],
                diff["characters_appeared"].get("new_characters"),
            ]
        )
        return diff

    @classmethod
    def _detect_cultivation(cls, text: str) -> List[Dict[str, str]]:
        changes: List[Dict[str, str]] = []
        seen = set()
        for pattern in cls.CULTIVATION_PATTERNS:
            for match in re.finditer(pattern, text):
                realm = match.group(1)
                stage = match.group(2) if match.lastindex and match.lastindex >= 2 else "未知"
                key = (realm, stage)
                if key in seen:
                    continue
                seen.add(key)
                changes.append({"realm": realm, "stage": stage, "source": match.group()})
        return changes

    @classmethod
    def _detect_items(cls, text: str) -> List[str]:
        items: List[str] = []
        for pattern in cls.ITEM_ACQUIRE_PATTERNS:
            for match in re.finditer(pattern, text):
                if match.lastindex and match.group(match.lastindex):
                    items.append(match.group(match.lastindex).strip())
        return list(dict.fromkeys(items))

    @classmethod
    def _detect_characters(cls, text: str, existing_state: Dict[str, Any]) -> Dict[str, Any]:
        mentioned: set[str] = set()
        for pattern in cls.DIALOGUE_NAME_PATTERNS:
            for match in re.finditer(pattern, text):
                name = next((g.strip() for g in match.groups() if g), "")
                if name and 2 <= len(name) <= 6:
                    mentioned.add(name)

        characters = existing_state.get("characters", {})
        existing_names = set(characters.keys())
        for char_id, data in characters.items():
            if isinstance(data, dict) and data.get("name"):
                existing_names.add(str(data["name"]))

        new_chars = sorted(name for name in mentioned if name not in existing_names)
        return {"all_mentioned": sorted(mentioned), "new_characters": new_chars}

    @classmethod
    def _extract_key_events(cls, text: str) -> List[str]:
        events: List[str] = []
        for match in re.finditer(r"【[^】]{4,80}】", text):
            events.append(match.group())
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in reversed(lines[-8:]):
            if any(marker in line for marker in ("？", "！", "……", "突然", "却", "然而")):
                events.append(line[:100])
                break
        return events[:5]


class ProjectState:
    """项目数据状态机 — 委托 ConfigManager 读写，保持 schema 一致。"""

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root)
        self.layout = ProjectLayout(self.root)
        self.config_manager = ConfigManager(self.root)
        self._hooks: Dict[str, List[Callable]] = {
            "before_outline": [],
            "after_draft": [],
            "before_finalize": [],
            "after_finalize": [],
            "after_volume": [],
        }

    def register_hook(self, event: str, fn: Callable) -> None:
        if event in self._hooks:
            self._hooks[event].append(fn)

    def trigger(self, event: str, **kwargs) -> List[Any]:
        results = []
        for fn in self._hooks.get(event, []):
            try:
                results.append(fn(**kwargs))
            except Exception as exc:
                results.append({"error": str(exc)})
        return results

    def load_all(self) -> Dict[str, Any]:
        return {
            "workflow_state": self.config_manager.load_workflow_state(),
            "character_cards": self.config_manager.load_character_cards(),
            "novel_writer_config": self.config_manager.load_config(),
            "voice_config": self.config_manager.load_voice_config(),
        }

    def sync_after_chapter(
        self,
        chapter_num: int,
        chapter_title: str,
        chapter_text: str,
        word_count: int,
    ) -> Dict[str, Any]:
        state = self.load_all()
        report: Dict[str, Any] = {
            "chapter": chapter_num,
            "title": chapter_title,
            "changes": {},
        }

        diff = ChapterDiff.detect(chapter_text, state.get("character_cards", {}))
        report["diff"] = diff

        char_updates: Dict[str, Any] = {}
        for name in diff.get("characters_appeared", {}).get("new_characters", []):
            char_updates[name] = {
                "name": name,
                "first_appearance": f"第{chapter_num}章",
                "current_status": {"location": "未知", "note": f"第{chapter_num}章首次提及"},
            }

        protagonist_id = self._find_protagonist_id(state.get("character_cards", {}))
        if protagonist_id and diff.get("cultivation_changes"):
            change = diff["cultivation_changes"][0]
            char_updates[protagonist_id] = {
                "current_status": {
                    "power_level": f"{change['realm']} {change['stage']}",
                }
            }

        if char_updates:
            sync_result = self.config_manager.sync_characters_from_chapter(
                chapter_num=chapter_num,
                character_updates=char_updates,
            )
            report["changes"]["character_cards"] = sync_result

        config = state.get("novel_writer_config", {})
        if diff.get("cultivation_changes") and config.get("protagonist"):
            change = diff["cultivation_changes"][0]
            config.setdefault("protagonist", {})["power_level"] = f"{change['realm']} {change['stage']}"
            self.config_manager.save_config(config)
            report["changes"]["novel_writer_config"] = {"power_level_updated": True}

        report["changes"]["workflow_state"] = {
            "note": "workflow 由 ConfigManager.finalize_chapter 维护，此处不重复写入",
        }
        report["hooks_triggered"] = len(
            self.trigger("after_finalize", chapter_num=chapter_num, diff=diff)
        )
        return report

    def verify_preflight(self, chapter_num: int) -> Dict[str, Any]:
        preflight = self.config_manager.validate_preflight(chapter_num=chapter_num)
        checks = {
            "ready": preflight["ready"],
            "blockers": list(preflight.get("blockers", [])),
            "warnings": list(preflight.get("warnings", [])),
            "config_status": {},
        }

        for key in ("novel_writer_config", "progress", "workflow_state", "voice_config", "character_cards"):
            path = self.layout.resolve_config(key)
            checks["config_status"][key] = {
                "exists": path is not None,
                "path": str(path) if path else None,
            }

        prev_final = self.layout.final_dir / f"chapter-{chapter_num - 1:03d}-final.md"
        if prev_final.exists():
            prev_content = prev_final.read_text(encoding="utf-8")
            if self._detect_over_scope(prev_content):
                checks["warnings"].append(
                    f"第{chapter_num - 1}章终稿可能覆盖第{chapter_num}章规划节拍，建议执行前章溢出 5 步法"
                )

        return checks

    @staticmethod
    def _find_protagonist_id(cards: Dict[str, Any]) -> Optional[str]:
        characters = cards.get("characters", {})
        for char_id, data in characters.items():
            if isinstance(data, dict) and data.get("current_status", {}).get("is_protagonist"):
                return char_id
        for char_id in ("protagonist", "main", "hero"):
            if char_id in characters:
                return char_id
        return None

    @staticmethod
    def _detect_over_scope(text: str) -> bool:
        endings = ("本章完", "一切归于平静", "暂时告一段落", "尘埃落定", "重归平静")
        tail = text[-200:] if len(text) > 200 else text
        return any(item in tail for item in endings)
