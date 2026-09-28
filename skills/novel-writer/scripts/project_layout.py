"""
Unified project directory layout for novel-writer.

All modules MUST resolve paths through ProjectLayout to avoid doc/code drift.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


class JsonLoadError(Exception):
    """Raised when a required JSON file exists but cannot be parsed."""

    def __init__(self, path: Path, cause: Exception):
        self.path = path
        self.cause = cause
        super().__init__(f"JSON 解析失败：{path} — {cause}")


class ProjectLayout:
    CONFIG_DIR = "config"
    PLANNING_DIR = "planning"
    PLOT_ENGINE_DIR = "plot_engine"
    FINAL_DIR = "final"

    CONFIG_FILES = {
        "novel_writer_config": "novel_writer_config.json",
        "progress": "progress.json",
        "workflow_state": "workflow_state.json",
        "voice_config": "voice_config.json",
        "character_cards": "character_cards.json",
        "creative_workflow": "creative_workflow.json",
        "author_profile": "author_profile.json",
    }

    ROOT_ARTIFACTS = {
        "world_hooks": "world_hooks.md",
        "volume_arc": "volume_arc.md",
    }

    LEGACY_ROOT_CONFIG = tuple(CONFIG_FILES.values())
    LEGACY_PLOT_PATTERNS = (
        "chapter_beats*.md",
        "plot_workshop*.json",
        "plot_engine*.md",
    )

    def __init__(self, run_dir: Path | str):
        self.run_dir = Path(run_dir)
        self.config_dir = self.run_dir / self.CONFIG_DIR
        self.planning_dir = self.run_dir / self.PLANNING_DIR
        self.plot_engine_dir = self.run_dir / self.PLOT_ENGINE_DIR
        self.final_dir = self.run_dir / self.FINAL_DIR

    def ensure_dirs(self) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.planning_dir.mkdir(parents=True, exist_ok=True)
        self.plot_engine_dir.mkdir(parents=True, exist_ok=True)
        self.final_dir.mkdir(parents=True, exist_ok=True)

    def ensure_volume_planning_dirs(self, volume_num: int) -> Path:
        volume_dir = self.volume_planning_dir(volume_num)
        volume_dir.mkdir(parents=True, exist_ok=True)
        (volume_dir / "events").mkdir(parents=True, exist_ok=True)
        return volume_dir

    def volume_planning_dir(self, volume_num: int) -> Path:
        return self.planning_dir / f"volume_{int(volume_num)}"

    def book_volume_plan_path(self) -> Path:
        return self.planning_dir / "book_volume_plan.md"

    def book_volume_plan_json_path(self) -> Path:
        return self.planning_dir / "book_volume_plan.json"

    def volume_outline_path(self, volume_num: int) -> Path:
        return self.volume_planning_dir(volume_num) / "volume_outline.md"

    def volume_event_plan_path(self, volume_num: int) -> Path:
        return self.volume_planning_dir(volume_num) / "volume_event_plan.json"

    def event_outline_path(self, volume_num: int, event_id: str) -> Path:
        safe_id = str(event_id).strip().lower()
        return self.volume_planning_dir(volume_num) / "events" / f"event_{safe_id}_outline.md"

    def plot_workshop_volume_path(self, volume_num: int) -> Path:
        return self.plot_engine_dir / f"plot_workshop_volume_{int(volume_num)}.json"

    def plot_workshop_event_path(self, volume_num: int, event_id: str) -> Path:
        safe_id = str(event_id).strip().lower()
        return self.plot_engine_dir / f"plot_workshop_event_{safe_id}.json"

    def plot_engine_volume_path(self, volume_num: int) -> Path:
        return self.plot_engine_dir / f"plot_engine_volume_{int(volume_num)}.md"

    def plot_engine_event_path(self, volume_num: int, event_id: str) -> Path:
        safe_id = str(event_id).strip().lower()
        return self.plot_engine_dir / f"plot_engine_event_{safe_id}.md"

    def config_path(self, key: str) -> Path:
        if key not in self.CONFIG_FILES:
            raise KeyError(f"Unknown config key: {key}")
        return self.config_dir / self.CONFIG_FILES[key]

    def root_artifact_path(self, key: str) -> Path:
        if key not in self.ROOT_ARTIFACTS:
            raise KeyError(f"Unknown root artifact: {key}")
        return self.run_dir / self.ROOT_ARTIFACTS[key]

    def plot_engine_path(self, file_name: str) -> Path:
        return self.plot_engine_dir / file_name

    def resolve_config(self, key: str) -> Optional[Path]:
        canonical = self.config_path(key)
        if canonical.exists():
            return canonical
        legacy = self.run_dir / self.CONFIG_FILES[key]
        if legacy.exists():
            return legacy
        return None

    def resolve_root_artifact(self, key: str) -> Optional[Path]:
        canonical = self.root_artifact_path(key)
        if canonical.exists():
            return canonical
        return None

    def glob_plot_engine(self, patterns: Sequence[str]) -> List[Path]:
        results: List[Path] = []
        search_roots = [self.plot_engine_dir, self.run_dir]
        for root in search_roots:
            if not root.exists():
                continue
            for pattern in patterns:
                results.extend(root.glob(pattern))
        unique = sorted(
            {p.resolve() for p in results if p.is_file()},
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return unique

    def migrate_legacy_layout(self) -> Dict[str, Any]:
        """Move legacy root-level files into standard directories (best-effort)."""
        self.ensure_dirs()
        moved: List[str] = []

        for key in self.CONFIG_FILES:
            legacy = self.run_dir / self.CONFIG_FILES[key]
            target = self.config_path(key)
            if legacy.exists() and not target.exists() and legacy.resolve() != target.resolve():
                shutil.move(str(legacy), str(target))
                moved.append(str(target.relative_to(self.run_dir)))

        for pattern in self.LEGACY_PLOT_PATTERNS:
            for legacy_file in self.run_dir.glob(pattern):
                target = self.plot_engine_dir / legacy_file.name
                if not target.exists():
                    shutil.move(str(legacy_file), str(target))
                    moved.append(str(target.relative_to(self.run_dir)))

        return {"migrated": moved, "count": len(moved)}

    def load_json(
        self,
        path: Path,
        default: Any = None,
        *,
        required: bool = False,
    ) -> Any:
        if not path.exists():
            if required:
                raise FileNotFoundError(f"缺少必需文件：{path}")
            from copy import deepcopy

            return deepcopy(default)

        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            if required:
                raise JsonLoadError(path, exc) from exc
            from copy import deepcopy

            return deepcopy(default)
