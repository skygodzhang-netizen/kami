"""
Config Manager - Manages book configuration and progress
"""
import json
import os
import re
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from .project_layout import JsonLoadError, ProjectLayout
    from .event_planning import EventPlanner, merge_event_config
    from .book_planning import BookPlanner
except ImportError:
    from project_layout import JsonLoadError, ProjectLayout
    from event_planning import EventPlanner, merge_event_config
    from book_planning import BookPlanner


class ConfigManager:
    def __init__(self, run_dir):
        self.run_dir = Path(run_dir)
        self.layout = ProjectLayout(self.run_dir)
        self.layout.ensure_dirs()
        self._json_errors: List[str] = []
        migration = self.layout.migrate_legacy_layout()
        self._last_migration = migration

    def load_config(self):
        path = self.layout.resolve_config("novel_writer_config")
        return self._load_json_at(path, {}) if path else {}

    def save_config(self, config):
        self._save_json_path(self.layout.config_path("novel_writer_config"), config)

    def load_progress(self):
        path = self.layout.resolve_config("progress")
        return self._load_json_at(path, {}) if path else {}

    def save_progress(self, progress):
        self._save_json_path(self.layout.config_path("progress"), progress)

    def load_workflow_state(self):
        path = self.layout.resolve_config("workflow_state")
        data = self._load_json_at(path, {"chapters": {}}) if path else {"chapters": {}}
        return self._normalize_workflow_state(data)

    def save_workflow_state(self, workflow_state):
        self._save_json_path(
            self.layout.config_path("workflow_state"),
            self._normalize_workflow_state(workflow_state),
        )

    def get_event_planner(self) -> EventPlanner:
        return EventPlanner(self.layout, self.load_config())

    def get_book_planner(self) -> BookPlanner:
        return BookPlanner(self.layout, self.load_config())

    def get_event_config(self) -> Dict[str, Any]:
        return merge_event_config(self.load_config())

    def load_creative_workflow(self) -> Dict[str, Any]:
        path = self.layout.resolve_config("creative_workflow")
        default = {
            "phase": "pre_init",
            "beats_confirmed": False,
            "beats_confirmed_at": None,
            "notes": "",
        }
        return self._load_json_at(path, default) if path else deepcopy(default)

    def save_creative_workflow(self, data: Dict[str, Any]) -> None:
        self._save_json_path(self.layout.config_path("creative_workflow"), data)

    def validate_pre_init_gate(self, *, force: bool = False) -> Dict[str, Any]:
        creative = self.load_creative_workflow()
        config = self.load_config()
        beats_path = self.find_chapter_beats_file()
        blockers: List[str] = []
        if force:
            return {"ready": True, "blockers": [], "creative_workflow": creative}
        if config.get("pre_init_completed") or creative.get("beats_confirmed"):
            return {"ready": True, "blockers": [], "creative_workflow": creative}
        if not beats_path:
            blockers.append(
                "全新项目须先完成 Pre-Init 创意咨询并确认全章节拍表，再执行 init。"
                "若已有确认版节拍表，请设置 creative_workflow.beats_confirmed=true 或 init(force=True)。"
            )
        event_cfg = merge_event_config(config)
        if event_cfg.get("require_book_volume_plan_at_pre_init") and not self.get_book_planner().has_book_plan():
            blockers.append(
                "本项目要求 Pre-Init 前完成全书卷规划。"
                "请执行 plan_book_volumes，或设置 require_book_volume_plan_at_pre_init=false。"
            )
        return {"ready": not blockers, "blockers": blockers, "creative_workflow": creative}

    def mark_pre_init_complete(self, notes: Optional[str] = None) -> Dict[str, Any]:
        creative = self.load_creative_workflow()
        creative.update(
            {
                "phase": "ready_for_init",
                "beats_confirmed": True,
                "beats_confirmed_at": self._get_timestamp(),
            }
        )
        if notes:
            creative["notes"] = notes
        self.save_creative_workflow(creative)
        config = self.load_config()
        config["pre_init_completed"] = True
        self.save_config(config)
        return creative

    def load_voice_config(self) -> Dict[str, Any]:
        """加载声音配置（支持 voice_config.json；兼容旧版 writing_style.json 文件名）"""
        config_path = self.find_file(["voice_config.json", "writing_style.json"])
        if not config_path:
            return {}
        return self.normalize_voice_config(self._load_json_at(config_path, {}))

    @staticmethod
    def author_profile_template_path() -> Path:
        return Path(__file__).resolve().parent.parent / "references" / "author_profile.template.json"

    def load_author_profile(self) -> Dict[str, Any]:
        path = self.layout.resolve_config("author_profile")
        default: Dict[str, Any] = {}
        template_path = self.author_profile_template_path()
        if template_path.exists():
            default = self._load_json_at(template_path, {})
        if not path:
            return deepcopy(default) if default else {}
        loaded = self._load_json_at(path, default)
        return self._normalize_author_profile(loaded, default)

    def save_author_profile(self, profile: Dict[str, Any]) -> None:
        self._save_json_path(
            self.layout.config_path("author_profile"),
            self._normalize_author_profile(profile),
        )

    def ensure_author_profile(self) -> Dict[str, Any]:
        path = self.layout.config_path("author_profile")
        if path.exists():
            return self.load_author_profile()
        template_path = self.author_profile_template_path()
        profile = self._load_json_at(template_path, {}) if template_path.exists() else {}
        profile = self._normalize_author_profile(profile)
        self.save_author_profile(profile)
        return profile

    def resolve_genre(
        self,
        explicit: Optional[str] = None,
        *,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> str:
        kwargs = kwargs or {}
        for candidate in (
            explicit,
            kwargs.get("genre"),
            self.load_config().get("genre"),
            self.load_author_profile().get("default_genre"),
        ):
            if candidate is not None and str(candidate).strip():
                return str(candidate).strip()
        return "未指定"

    def resolve_core_pleasure(
        self,
        explicit: Optional[str] = None,
        *,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> str:
        kwargs = kwargs or {}
        config = self.load_config()
        profile = self.load_author_profile()
        for candidate in (
            explicit,
            kwargs.get("core_pleasure"),
            config.get("default_core_pleasure"),
            config.get("core_pleasure"),
            profile.get("default_core_pleasure"),
        ):
            if candidate is not None and str(candidate).strip():
                return str(candidate).strip()
        return "未指定"

    def merge_author_profile_into_voice_config(self, voice_config: Dict[str, Any]) -> Dict[str, Any]:
        """作者签名来自 author_profile，跨项目一致；覆盖 LLM 对签名字段的漂移。"""
        if not isinstance(voice_config, dict):
            return {}
        merged = deepcopy(voice_config)
        profile = self.load_author_profile()
        if not profile:
            return merged
        signature = profile.get("author_signature")
        if signature:
            merged["author_signature"] = deepcopy(signature)
        policy = profile.get("mature_content_policy")
        if policy:
            merged["mature_content_policy"] = deepcopy(policy)
        meta = merged.setdefault("_meta", {})
        if isinstance(meta, dict):
            if profile.get("author_id"):
                meta["author_id"] = profile["author_id"]
            if profile.get("display_name"):
                meta["author_display_name"] = profile["display_name"]
        return merged

    def _normalize_author_profile(
        self,
        profile: Dict[str, Any],
        template: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        base = deepcopy(template or {})
        if not isinstance(profile, dict):
            return base
        normalized = deepcopy(base)
        normalized.update({k: v for k, v in profile.items() if v is not None})
        if "author_signature" in profile and isinstance(profile["author_signature"], dict):
            sig = deepcopy(base.get("author_signature", {}))
            sig.update(profile["author_signature"])
            normalized["author_signature"] = sig
        if "mature_content_policy" in profile and isinstance(profile["mature_content_policy"], dict):
            pol = deepcopy(base.get("mature_content_policy", {}))
            pol.update(profile["mature_content_policy"])
            normalized["mature_content_policy"] = pol
        return normalized

    def get_context_snapshot(
        self,
        chapter_num: Optional[int] = None,
        explicit_current_arc: Optional[str] = None,
    ) -> Dict[str, Any]:
        progress = self.load_progress()
        config = self.load_config()
        world_hooks_path = self.find_file(["world_hooks.md"])
        volume_arc_path = self.find_file(["volume_*_outline.md", "volume_arc.md"])
        book_plan_path = self.layout.book_volume_plan_path()
        book_plan_json_path = self.layout.book_volume_plan_json_path()
        chapter_beats_path = self.find_chapter_beats_file(chapter_num)
        # 支持新的 voice_config.json 和旧的 writing_style.json
        voice_config_path = self.find_file(["voice_config.json", "writing_style.json"])
        plot_workshop_path = self.find_plot_workshop_file(chapter_num)
        plot_engine_path = self.find_plot_engine_file(chapter_num)

        voice_config = self.normalize_voice_config(
            self._load_json_at(voice_config_path, {}) if voice_config_path else {}
        )
        character_cards = self.load_character_cards()
        plot_workshop = self._load_json_at(plot_workshop_path, {}) if plot_workshop_path else {}
        plot_engine = self.read_text(plot_engine_path)
        
        snapshot = {
            "progress": progress,
            "config": config,
            "progress_path": self._string_path(self.layout.resolve_config("progress")),
            "config_path": self._string_path(self.layout.resolve_config("novel_writer_config")),
            "character_cards_path": self._string_path(self.layout.resolve_config("character_cards")),
            "world_hooks_path": self._string_path(world_hooks_path),
            "world_hooks": self.read_text(world_hooks_path),
            "volume_arc_path": self._string_path(volume_arc_path),
            "volume_arc": self.read_text(volume_arc_path),
            "book_volume_plan_path": self._string_path(book_plan_path if book_plan_path.exists() else None),
            "book_volume_plan_json_path": self._string_path(
                book_plan_json_path if book_plan_json_path.exists() else None
            ),
            "book_volume_plan": self.read_text(book_plan_path if book_plan_path.exists() else None),
            "book_volume_plan_json": self._load_json_at(
                book_plan_json_path if book_plan_json_path.exists() else None, {}
            ),
            "chapter_beats_path": self._string_path(chapter_beats_path),
            "chapter_beats": self.read_text(chapter_beats_path),
            "voice_config_path": self._string_path(voice_config_path),
            "voice_config": voice_config,
            "plot_workshop_path": self._string_path(plot_workshop_path),
            "plot_workshop": plot_workshop,
            "plot_engine_path": self._string_path(plot_engine_path),
            "plot_engine": plot_engine,
            "character_cards": character_cards,
            # 保留旧字段兼容
            "writing_style_path": self._string_path(voice_config_path),
            "writing_style": voice_config,
            "current_arc_name": explicit_current_arc or self._extract_current_arc_name(progress, config),
        }
        snapshot["relationship_context"] = self.build_relationship_context(character_cards)
        snapshot["faction_context"] = self.build_faction_context(character_cards)
        snapshot["trope_hint"] = self.extract_trope_hint(plot_workshop)
        snapshot["progress_node"] = self.infer_progress_node(chapter_num, snapshot["chapter_beats"])
        snapshot["chapter_workflow"] = self.get_chapter_workflow(chapter_num) if chapter_num is not None else {}
        snapshot["event_config"] = self.get_event_config()
        planner = self.get_event_planner()
        volume_num = self._to_int(config.get("current_volume")) or 1
        snapshot["event_planning_active"] = planner.uses_event_planning(volume_num)
        snapshot["legacy_event_mode"] = planner.is_legacy_mode(volume_num)
        if chapter_num is not None and snapshot["event_planning_active"]:
            event_ctx = planner.validate_event_preflight(volume_num, int(chapter_num))
            snapshot["event_context"] = event_ctx
            if event_ctx.get("event"):
                snapshot["current_event"] = event_ctx["event"]
                snapshot["current_event_id"] = event_ctx.get("event_id")
                outline_path = event_ctx.get("event_outline_path")
                snapshot["event_outline_path"] = outline_path
                snapshot["event_outline"] = self.read_text(Path(outline_path)) if outline_path else ""
        snapshot["consistency"] = self.validate_consistency(snapshot, chapter_num)
        return snapshot

    def validate_preflight(
        self,
        chapter_num: Optional[int] = None,
        explicit_current_arc: Optional[str] = None,
    ) -> Dict[str, Any]:
        snapshot = self.get_context_snapshot(chapter_num=chapter_num, explicit_current_arc=explicit_current_arc)
        blockers = []
        warnings = []

        required_files = {
            "world_hooks.md": snapshot["world_hooks_path"],
            "volume_arc.md": snapshot["volume_arc_path"],
            "plot_engine/chapter_beats_*.md": snapshot["chapter_beats_path"],
            "config/voice_config.json": snapshot["voice_config_path"],
            "config/character_cards.json": snapshot.get("character_cards_path"),
            "config/progress.json": snapshot["progress_path"],
            "config/novel_writer_config.json": snapshot["config_path"],
        }
        for name, path in required_files.items():
            if not path:
                blockers.append(f"缺少必需文件：{name}")

        blockers.extend(self._json_errors)
        self._json_errors = []

        consistency = snapshot["consistency"]
        blockers.extend(consistency["blockers"])
        warnings.extend(consistency["warnings"])

        config = snapshot.get("config") or {}
        volume_num = self._to_int(config.get("current_volume")) or 1
        event_cfg = merge_event_config(config)
        if chapter_num is not None and snapshot.get("event_planning_active"):
            planner = self.get_event_planner()
            event_check = planner.validate_event_preflight(volume_num, int(chapter_num))
            blockers.extend(event_check.get("blockers", []))
            warnings.extend(event_check.get("warnings", []))

        if (
            snapshot.get("event_planning_active")
            and not snapshot.get("legacy_event_mode")
            and not snapshot.get("book_volume_plan_path")
            and event_cfg.get("event_planning_enabled")
        ):
            warnings.append(
                "新项目建议先执行 plan_book_volumes 生成全书卷规划，再进入各卷事件编排。"
            )

        return {
            "ready": not blockers,
            "blockers": blockers,
            "warnings": warnings,
            "snapshot": snapshot,
        }

    def validate_consistency(self, snapshot: Dict[str, Any], chapter_num: Optional[int] = None) -> Dict[str, List[str]]:
        progress = snapshot.get("progress") or {}
        config = snapshot.get("config") or {}
        chapter_beats = snapshot.get("chapter_beats") or ""
        current_arc_name = snapshot.get("current_arc_name")
        blockers: List[str] = []
        warnings: List[str] = []

        config_current_chapter = self._to_int(config.get("current_chapter"))
        progress_current_chapter = self._to_int(progress.get("current_chapter"))
        progress_completed_chapters = self._to_int(progress.get("current_chapters"))

        if chapter_num is not None:
            allowed_values = {chapter_num, chapter_num - 1}
            if config_current_chapter is not None and config_current_chapter not in allowed_values:
                warnings.append(
                    f"novel_writer_config.json 的 current_chapter={config_current_chapter}，与当前写作章节 {chapter_num} 不一致"
                )
            if progress_current_chapter is not None and progress_current_chapter not in allowed_values | {chapter_num + 1}:
                warnings.append(
                    f"progress.json 的 current_chapter={progress_current_chapter}，与当前写作章节 {chapter_num} 不一致"
                )
            if progress_completed_chapters is not None and progress_completed_chapters not in {chapter_num - 1, chapter_num}:
                warnings.append(
                    f"progress.json 的 current_chapters={progress_completed_chapters}，与当前写作章节 {chapter_num} 不一致"
                )

        if current_arc_name and chapter_beats and current_arc_name not in chapter_beats:
            blockers.append(f"current_arc={current_arc_name} 未在篇章管理器中出现")

        volume_arc = snapshot.get("volume_arc") or ""
        if current_arc_name and volume_arc and current_arc_name not in volume_arc:
            warnings.append(f"current_arc={current_arc_name} 未在卷大纲中出现")

        progress_node = snapshot.get("progress_node")
        if chapter_num is not None and not progress_node:
            blockers.append(f"篇章管理器未找到第 {chapter_num} 章对应节点")

        return {"blockers": blockers, "warnings": warnings}

    def get_chapter_workflow(self, chapter_num: Optional[int]) -> Dict[str, Any]:
        if chapter_num is None:
            return {}
        workflow_state = self.load_workflow_state()
        chapter_state = workflow_state.get("chapters", {}).get(str(chapter_num))
        return deepcopy(chapter_state or self._default_chapter_workflow(chapter_num))

    def validate_chapter_workflow(self, chapter_num: int, target_phase: str) -> Dict[str, Any]:
        chapter_state = self.get_chapter_workflow(chapter_num)
        blockers: List[str] = []
        warnings: List[str] = []

        outline_status = chapter_state.get("outline", {}).get("status")
        draft_status = chapter_state.get("draft", {}).get("status")
        final_status = chapter_state.get("final", {}).get("status")

        if final_status == "completed" and target_phase in {"outline", "draft", "finalize"}:
            blockers.append(f"第 {chapter_num} 章已完成终稿入库，禁止跳过流程重复写作。")

        if target_phase == "draft":
            if outline_status != "confirmed":
                blockers.append("单章大纲尚未确认，禁止生成正文。")
            if not chapter_state.get("outline", {}).get("content"):
                blockers.append("缺少已确认的单章大纲内容。")

        if target_phase == "finalize":
            if outline_status != "confirmed":
                blockers.append("单章大纲尚未确认，禁止终稿入库。")
            if draft_status != "confirmed":
                blockers.append("篇章草稿尚未确认，禁止终稿入库。")
            if not chapter_state.get("draft", {}).get("content"):
                blockers.append("缺少已确认的篇章草稿内容。")

        return {
            "ready": not blockers,
            "blockers": blockers,
            "warnings": warnings,
            "chapter_workflow": chapter_state,
        }

    def record_generated_outline(
        self,
        chapter_num: int,
        outline: str,
        prompt: str,
        requested_word_count: int,
        word_limits: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        workflow_state = self.load_workflow_state()
        chapter_state = self._get_or_create_chapter_workflow(workflow_state, chapter_num)
        chapter_state["outline"] = {
            "status": "generated",
            "content": outline,
            "prompt": prompt,
            "requested_word_count": requested_word_count,
            "word_limits": deepcopy(word_limits or {}),
        }
        chapter_state["draft"] = self._default_stage_state()
        chapter_state["final"] = self._default_final_stage_state()
        self.save_workflow_state(workflow_state)
        return deepcopy(chapter_state)

    def confirm_outline(
        self,
        chapter_num: int,
        outline_text: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        workflow_state = self.load_workflow_state()
        chapter_state = self._get_or_create_chapter_workflow(workflow_state, chapter_num)
        content = (outline_text or chapter_state["outline"].get("content") or "").strip()
        if not content:
            raise ValueError(f"第 {chapter_num} 章缺少可确认的单章大纲内容")

        outline_state = deepcopy(chapter_state["outline"])
        previous_content = outline_state.get("content") or ""
        outline_state["status"] = "confirmed"
        outline_state["content"] = content
        if notes:
            outline_state["notes"] = notes
        chapter_state["outline"] = outline_state

        if previous_content != content:
            chapter_state["draft"] = self._default_stage_state()
            chapter_state["final"] = self._default_final_stage_state()

        self.save_workflow_state(workflow_state)
        return deepcopy(chapter_state)

    def record_generated_draft(
        self,
        chapter_num: int,
        draft: str,
        prompt: str,
        word_report: Dict[str, Any],
        validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        workflow_state = self.load_workflow_state()
        chapter_state = self._get_or_create_chapter_workflow(workflow_state, chapter_num)
        chapter_state["draft"] = {
            "status": "generated",
            "content": draft,
            "prompt": prompt,
            "word_report": deepcopy(word_report),
            "validation": deepcopy(validation),
        }
        chapter_state["final"] = self._default_final_stage_state()
        self.save_workflow_state(workflow_state)
        return deepcopy(chapter_state)

    def confirm_draft(
        self,
        chapter_num: int,
        draft_text: Optional[str] = None,
        notes: Optional[str] = None,
        word_report: Optional[Dict[str, Any]] = None,
        validation: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        workflow_state = self.load_workflow_state()
        chapter_state = self._get_or_create_chapter_workflow(workflow_state, chapter_num)
        content = (draft_text or chapter_state["draft"].get("content") or "").strip()
        if not content:
            raise ValueError(f"第 {chapter_num} 章缺少可确认的篇章草稿内容")

        draft_state = deepcopy(chapter_state["draft"])
        previous_content = draft_state.get("content") or ""
        draft_state["status"] = "confirmed"
        draft_state["content"] = content
        if word_report is not None:
            draft_state["word_report"] = deepcopy(word_report)
        if validation is not None:
            draft_state["validation"] = deepcopy(validation)
        if notes:
            draft_state["notes"] = notes
        chapter_state["draft"] = draft_state

        if previous_content != content:
            chapter_state["final"] = self._default_final_stage_state()

        self.save_workflow_state(workflow_state)
        return deepcopy(chapter_state)

    def finalize_chapter(
        self,
        chapter_num: int,
        final_text: str,
        word_count: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        metadata = metadata or {}
        progress = deepcopy(self.load_progress())
        config = deepcopy(self.load_config())

        self._set_numeric_field(progress, "current_chapters", chapter_num)
        self._set_numeric_field(progress, "current_chapter", chapter_num + 1)
        # Re-finalizing a chapter replaces its contribution instead of counting it twice.
        # The final chapter files are the source of truth for completed chapter words.
        other_words = 0
        final_name = f"chapter-{chapter_num:03d}-final.md"
        for prior_file in self.layout.final_dir.glob("chapter-*-final.md"):
            if prior_file.name == final_name:
                continue
            other_words += sum("\u4e00" <= char <= "\u9fff" for char in prior_file.read_text(encoding="utf-8"))
        self._set_numeric_field(progress, "current_words", other_words + word_count)

        target_words = (
            self._to_int(progress.get("target_words"))
            or self._to_int(config.get("target_words"))
            or self._to_int(metadata.get("target_words"))
        )
        if target_words and target_words > 0:
            progress["completion_rate"] = round(progress.get("current_words", 0) / target_words, 4)

        current_arc = progress.setdefault("current_arc", {})
        override_arc = metadata.get("current_arc") or {}
        if override_arc:
            if override_arc.get("name"):
                current_arc["name"] = override_arc["name"]
            if override_arc.get("description"):
                current_arc["description"] = override_arc["description"]
            if override_arc.get("reset_completed_chapters"):
                current_arc["completed_chapters"] = []

        completed_chapters = current_arc.setdefault("completed_chapters", [])
        if chapter_num not in completed_chapters:
            completed_chapters.append(chapter_num)
            completed_chapters.sort()

        character_progress_updates = metadata.get("character_progress") or {}
        if character_progress_updates:
            character_progress = progress.setdefault("character_progress", {})
            self._deep_merge(character_progress, character_progress_updates)

        self._set_numeric_field(config, "current_chapter", chapter_num + 1)
        
        # 多卷管理：动态 volume_{n}_progress
        current_volume = self._get_current_volume(config, chapter_num)
        volume_progress_key = f"volume_{current_volume}_progress"
        volume_progress = config.setdefault(volume_progress_key, {})
        self._set_numeric_field(
            volume_progress,
            "completed_chapters",
            max(self._to_int(volume_progress.get("completed_chapters")) or 0, chapter_num),
        )
        # 记录当前卷号
        config["current_volume"] = current_volume

        # ==================== 角色卡同步 ====================
        character_sync_result = None
        character_updates = metadata.get("character_updates") or metadata.get("character_progress")
        if character_updates:
            character_sync_result = self.sync_characters_from_chapter(chapter_num, character_updates)
        
        # 角色一致性检查
        character_validation = self.validate_character_consistency(chapter_num)
        
        self.save_progress(progress)
        self.save_config(config)

        # ==================== 卷管理检查点 ====================
        ten_chapter_checkpoint = self.build_ten_chapter_checkpoint(chapter_num)
        volume_checkpoint = self.build_volume_checkpoint(chapter_num)
        
        # 检查是否需要卷流转
        volume_transition = None
        if volume_checkpoint.get("transition_ready"):
            volume_transition = self.transition_to_next_volume(current_volume)
        
        update_log_entry = self._build_update_log_entry(
            chapter_num=chapter_num,
            word_count=word_count,
            metadata=metadata,
            checkpoint=ten_chapter_checkpoint,
        )
        self.append_update_log(update_log_entry)
        workflow_state = self.load_workflow_state()
        chapter_state = self._get_or_create_chapter_workflow(workflow_state, chapter_num)
        chapter_state["final"] = {
            "status": "completed",
            "content": final_text,
            "word_count": word_count,
        }
        self.save_workflow_state(workflow_state)

        return {
            "progress": progress,
            "config": config,
            "checkpoint": ten_chapter_checkpoint,
            "volume_checkpoint": volume_checkpoint,
            "update_log_entry": update_log_entry,
            "chapter_workflow": deepcopy(chapter_state),
            "character_sync": character_sync_result,
            "character_validation": character_validation,
            "volume_transition": volume_transition,
        }

    def append_update_log(self, entry: str) -> None:
        if not entry.strip():
            return
        update_log_path = self.run_dir / "update_log.md"
        existing = ""
        if update_log_path.exists():
            existing = update_log_path.read_text(encoding="utf-8").rstrip()
        new_content = entry.strip() if not existing else f"{existing}\n\n{entry.strip()}"
        self._atomic_write_text(update_log_path, f"{new_content}\n")

    def build_ten_chapter_checkpoint(self, chapter_num: int) -> Dict[str, Any]:
        due = chapter_num % 10 == 0
        # 从配置加载检查点项，如未配置则使用通用默认值
        config = self.load_config()
        default_items = [
            {"name": "篇章管理器同步", "required": due},
            {"name": "角色进度校验", "required": due},
            {"name": "剧情一致性检查", "required": due},
            {"name": "update_log 汇总", "required": due},
        ]
        custom_items = config.get("checkpoint_items")
        if custom_items and isinstance(custom_items, list):
            items = [{"name": item, "required": due} for item in custom_items]
        else:
            items = default_items
        return {"due": due, "items": items}

    def find_chapter_beats_file(self, chapter_num: Optional[int] = None) -> Optional[Path]:
        candidates = self.layout.glob_plot_engine(["chapter_beats*.md"])
        if not candidates:
            return None
        if chapter_num is None:
            return candidates[0]
        for candidate in candidates:
            start, end = self._extract_range(candidate.stem)
            if start is not None and end is not None and start <= chapter_num <= end:
                return candidate
        return candidates[0]

    def find_plot_workshop_file(self, chapter_num: Optional[int] = None) -> Optional[Path]:
        candidates = self.layout.glob_plot_engine(
            ["plot_workshop_chapter_*.json", "plot_workshop.json"]
        )
        if not candidates:
            return None
        if chapter_num is None:
            return candidates[0]
        for candidate in candidates:
            start, end = self._extract_range(candidate.stem)
            if start is not None and end is not None and start <= chapter_num <= end:
                return candidate
        return candidates[0]

    def find_plot_engine_file(self, chapter_num: Optional[int] = None) -> Optional[Path]:
        candidates = self.layout.glob_plot_engine(
            ["plot_engine_chapter_*.md", "plot_engine.md"]
        )
        if not candidates:
            return None
        if chapter_num is None:
            return candidates[0]
        for candidate in candidates:
            start, end = self._extract_range(candidate.stem)
            if start is not None and end is not None and start <= chapter_num <= end:
                return candidate
        return candidates[0]

    def find_file(self, patterns: Sequence[str]) -> Optional[Path]:
        artifact_by_name = {v: k for k, v in ProjectLayout.ROOT_ARTIFACTS.items()}
        config_by_name = {
            "novel_writer_config.json": "novel_writer_config",
            "progress.json": "progress",
            "workflow_state.json": "workflow_state",
            "voice_config.json": "voice_config",
            "writing_style.json": "voice_config",
            "author_profile.json": "author_profile",
            "character_cards.json": "character_cards",
        }
        for pattern in patterns:
            if pattern in artifact_by_name:
                resolved = self.layout.resolve_root_artifact(artifact_by_name[pattern])
                if resolved:
                    return resolved
            if pattern in config_by_name:
                resolved = self.layout.resolve_config(config_by_name[pattern])
                if resolved:
                    return resolved
        candidates = self._glob_sorted(patterns)
        return candidates[0] if candidates else None

    def read_text(self, path: Optional[Path]) -> str:
        if not path or not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def infer_progress_node(self, chapter_num: Optional[int], chapter_beats_content: str) -> str:
        if chapter_num is None or not chapter_beats_content:
            return ""
        nodes = self._extract_progress_nodes(chapter_beats_content)
        for node in nodes:
            start, end = self._extract_range(str(node.get("chapters", "")))
            if start is not None and end is not None and start <= chapter_num <= end:
                return self._dump_json(node)
        natural_node = self._extract_natural_language_progress_node(chapter_num, chapter_beats_content)
        if natural_node:
            return self._dump_json(natural_node)
        return ""

    def _load_json(self, file_ref: Any, default: Any) -> Any:
        path = file_ref if isinstance(file_ref, Path) else self.run_dir / str(file_ref)
        return self._load_json_at(path, default)

    def _load_json_at(self, path: Optional[Path], default: Any, *, strict: bool = False) -> Any:
        if path is None or not path.exists():
            return deepcopy(default)
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as exc:
            message = f"JSON 损坏无法解析：{path} — {exc}"
            self._json_errors.append(message)
            if strict:
                raise JsonLoadError(path, exc) from exc
            return deepcopy(default)
        except Exception as exc:
            message = f"读取失败：{path} — {exc}"
            self._json_errors.append(message)
            return deepcopy(default)

    def _save_json(self, file_name: str, data: Any) -> None:
        key_map = {
            "novel_writer_config.json": "novel_writer_config",
            "progress.json": "progress",
            "workflow_state.json": "workflow_state",
            "voice_config.json": "voice_config",
            "character_cards.json": "character_cards",
            "creative_workflow.json": "creative_workflow",
            "author_profile.json": "author_profile",
        }
        if file_name in key_map:
            self._save_json_path(self.layout.config_path(key_map[file_name]), data)
            return
        self._save_json_path(self.run_dir / file_name, data)

    def _save_json_path(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        self._atomic_write_text(path, f"{payload}\n")

    def _atomic_write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        os.replace(temp_path, path)

    def _glob_sorted(self, patterns: Sequence[str]) -> List[Path]:
        results: List[Path] = []
        search_roots = [self.run_dir, self.layout.config_dir, self.layout.plot_engine_dir]
        for root in search_roots:
            if not root.exists():
                continue
            for pattern in patterns:
                results.extend(root.glob(pattern))
                results.extend(root.rglob(pattern))
        unique_results = sorted(
            {path.resolve() for path in results if path.is_file()},
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return unique_results

    def _normalize_workflow_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy flat chapter_XXX keys into nested chapters schema."""
        if not isinstance(data, dict):
            return {"chapters": {}}
        if "chapters" in data and isinstance(data.get("chapters"), dict):
            return data

        chapters: Dict[str, Any] = {}
        meta_keys = {"current_chapter", "current_stage"}
        meta = {k: data[k] for k in meta_keys if k in data}

        for key, value in data.items():
            if not key.startswith("chapter_"):
                continue
            try:
                chapter_num = int(key.split("_", 1)[1])
            except (IndexError, ValueError):
                continue
            if isinstance(value, dict) and "outline" in value and isinstance(value["outline"], dict):
                chapters[str(chapter_num)] = value
                continue
            chapters[str(chapter_num)] = {
                "chapter_num": chapter_num,
                "outline": {
                    "status": "confirmed" if value.get("outline") == "completed" else "not_started",
                    "content": "",
                },
                "draft": {
                    "status": "confirmed" if value.get("draft") == "completed" else "not_started",
                    "content": "",
                },
                "final": {
                    "status": "completed" if value.get("final") == "completed" else "not_started",
                    "content": "",
                    "word_count": 0,
                },
            }
            if value.get("notes"):
                chapters[str(chapter_num)]["final"]["notes"] = value["notes"]

        normalized = {"chapters": chapters}
        normalized.update(meta)
        return normalized

    def _extract_current_arc_name(self, progress: Dict[str, Any], config: Dict[str, Any]) -> str:
        return (
            str(progress.get("current_arc", {}).get("name") or "").strip()
            or str(config.get("current_arc", {}).get("name") or "").strip()
        )

    def _extract_progress_nodes(self, chapter_beats_content: str) -> List[Dict[str, Any]]:
        raw_text = chapter_beats_content.strip()
        if not raw_text:
            return []
        fenced_match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
        candidate = fenced_match.group(1) if fenced_match else raw_text
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        return []

    def _extract_natural_language_progress_node(
        self,
        chapter_num: int,
        chapter_beats_content: str,
    ) -> Optional[Dict[str, Any]]:
        pattern = re.compile(
            r"(?:^|\n)(?:###\s*)?第\s*(\d+)\s*章[：:]\s*【([^】]+)】\s*(.*?)(?=\n(?:###\s*)?第\s*\d+\s*章[：:]|\Z)",
            re.S,
        )
        for match in pattern.finditer(chapter_beats_content):
            current_chapter = int(match.group(1))
            if current_chapter != chapter_num:
                continue

            emotion = match.group(2).strip()
            body = match.group(3).strip()
            node = {
                "chapter": current_chapter,
                "chapters": str(current_chapter),
                "emotion": emotion,
                "raw_text": body,
            }

            field_mapping = {
                "本章情绪目标": "emotion_goal",
                "情绪目标": "emotion_goal",
                "情绪起点": "emotion_start",
                "起点": "emotion_start",
                "情绪终点": "emotion_end",
                "终点": "emotion_end",
                "关键事件": "key_events",
                "爽点/钩子": "hook",
                "字数弹性": "word_range",
                "字数": "word_range",
            }
            for raw_line in body.splitlines():
                cleaned_line = raw_line.strip().lstrip("-").strip()
                if "：" not in cleaned_line:
                    continue
                label, value = cleaned_line.split("：", 1)
                key = field_mapping.get(label.strip())
                if key and value.strip():
                    node[key] = value.strip()
            return node
        return None

    def _extract_range(self, text: str) -> Sequence[Optional[int]]:
        matches = re.findall(r"(\d+)", text)
        if not matches:
            return None, None
        if len(matches) == 1:
            value = int(matches[0])
            return value, value
        return int(matches[0]), int(matches[1])

    def _set_numeric_field(self, mapping: Dict[str, Any], key: str, value: int) -> None:
        mapping[key] = int(value)

    def _increment_numeric_field(self, mapping: Dict[str, Any], key: str, amount: int) -> None:
        mapping[key] = int(self._to_int(mapping.get(key)) or 0) + int(amount)

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                self._deep_merge(target[key], value)
                continue
            target[key] = value

    def _build_update_log_entry(
        self,
        chapter_num: int,
        word_count: int,
        metadata: Dict[str, Any],
        checkpoint: Dict[str, Any],
    ) -> str:
        fixes = metadata.get("fixed_issues") or []
        next_actions = metadata.get("next_actions") or []
        lines = [
            f"## 第 {chapter_num} 章完成",
            f"- 正文字数：{word_count}",
        ]
        if fixes:
            lines.append(f"- 本章修正：{'；'.join(str(item) for item in fixes)}")
        if next_actions:
            lines.append(f"- 下一步：{'；'.join(str(item) for item in next_actions)}")
        if checkpoint.get("due"):
            # 从配置读取检查点项，使用通用描述
            config = self.load_config()
            checkpoint_items = config.get("checkpoint_items")
            if checkpoint_items and isinstance(checkpoint_items, list):
                items_str = "、".join(checkpoint_items)
            else:
                items_str = "篇章管理器、角色进度、剧情一致性"
            lines.append(f"- 10章检查点：已触发，请同步{items_str}")
        return "\n".join(lines)

    def _get_or_create_chapter_workflow(self, workflow_state: Dict[str, Any], chapter_num: int) -> Dict[str, Any]:
        chapters = workflow_state.setdefault("chapters", {})
        key = str(chapter_num)
        if key not in chapters:
            chapters[key] = self._default_chapter_workflow(chapter_num)
        return chapters[key]

    def _default_chapter_workflow(self, chapter_num: int) -> Dict[str, Any]:
        return {
            "chapter_num": chapter_num,
            "outline": self._default_stage_state(),
            "draft": self._default_stage_state(),
            "final": self._default_final_stage_state(),
        }

    def _default_stage_state(self) -> Dict[str, Any]:
        return {
            "status": "not_started",
            "content": "",
        }

    def _default_final_stage_state(self) -> Dict[str, Any]:
        return {
            "status": "not_started",
            "content": "",
            "word_count": 0,
        }

    def _dump_json(self, payload: Dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _string_path(self, path: Optional[Path]) -> Optional[str]:
        return str(path) if path else None

    def _to_int(self, value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def validate_voice_config(self, voice_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证 voice_config 配置格式
        返回验证结果：{"valid": bool, "errors": [...], "warnings": [...]}
        """
        errors = []
        warnings = []
        voice_config = self.normalize_voice_config(voice_config)
        
        if not isinstance(voice_config, dict):
            errors.append("voice_config 必须是字典类型")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        # 检查必需字段
        required_sections = ["narrative", "pacing", "description"]
        for section in required_sections:
            if section not in voice_config:
                warnings.append(f"voice_config 缺少推荐章节: {section}")
        
        # 检查字数阈值
        quality = voice_config.get("quality_thresholds", {})
        if "chapter_length" in quality:
            length = quality["chapter_length"]
            min_words = length.get("min", 0)
            max_words = length.get("max", 0)
            if min_words and max_words and min_words > max_words:
                errors.append(f"字数阈值错误: min ({min_words}) > max ({max_words})")
        
        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def extract_trope_hint(self, plot_workshop: Dict[str, Any]) -> str:
        if not isinstance(plot_workshop, dict):
            return ""
        selected_trope = plot_workshop.get("selected_trope", {})
        if isinstance(selected_trope, dict):
            return str(selected_trope.get("id") or selected_trope.get("name") or "").strip()
        return ""

    def normalize_voice_config(self, voice_config: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(voice_config, dict):
            return {}

        normalized = deepcopy(voice_config)
        quality = normalized.setdefault("quality_thresholds", {})
        chapter_length = quality.get("chapter_length", {})

        if isinstance(chapter_length, dict):
            min_words = self._to_int(chapter_length.get("min"))
            max_words = self._to_int(chapter_length.get("max"))
            target_value = chapter_length.get("target") or chapter_length.get("ideal")

            if min_words is not None and quality.get("min_chapter_words") is None:
                quality["min_chapter_words"] = min_words
            if max_words is not None and quality.get("max_chapter_words") is None:
                quality["max_chapter_words"] = max_words
            if quality.get("target_chapter_words") is None:
                target_words = self._parse_target_word_value(target_value)
                if target_words is not None:
                    quality["target_chapter_words"] = target_words

        return self.merge_author_profile_into_voice_config(normalized)

    def build_relationship_context(self, character_cards: Optional[Dict[str, Any]] = None) -> str:
        cards = character_cards or self.load_character_cards()
        relationships = cards.get("relationships", {})
        if not relationships:
            return "暂无已记录的角色关系。"

        lines = ["已记录关系摘要："]
        for relationship in list(relationships.values())[:12]:
            char_a = relationship.get("character_a", "未知角色")
            char_b = relationship.get("character_b", "未知角色")
            rel_type = relationship.get("type", "unknown")
            reverse_type = relationship.get("reverse_type")
            metrics = relationship.get("metrics", {})
            metric_summary = []
            for key in ("intimacy", "trust", "conflict"):
                if key in metrics:
                    metric_summary.append(f"{key}={metrics[key]}")
            relation_line = f"- {char_a} -> {char_b}: {rel_type}"
            if reverse_type and reverse_type != rel_type:
                relation_line += f" / {char_b} -> {char_a}: {reverse_type}"
            if metric_summary:
                relation_line += f" ({', '.join(metric_summary)})"
            lines.append(relation_line)
        return "\n".join(lines)

    def build_faction_context(self, character_cards: Optional[Dict[str, Any]] = None) -> str:
        cards = character_cards or self.load_character_cards()
        factions = cards.get("factions", {})
        if not factions:
            return "暂无已记录的阵营信息。"

        lines = ["已记录阵营摘要："]
        for faction in list(factions.values())[:8]:
            members = faction.get("members", [])
            enemies = faction.get("enemies", [])
            allies = faction.get("allies", [])
            lines.append(
                f"- {faction.get('name', faction.get('id', '未命名阵营'))}"
                f"（{faction.get('type', '未分类')}）"
                f"，成员：{', '.join(members[:6]) or '无'}"
                f"，敌对：{', '.join(enemies[:4]) or '无'}"
                f"，盟友：{', '.join(allies[:4]) or '无'}"
            )
        return "\n".join(lines)

    def _parse_target_word_value(self, value: Any) -> Optional[int]:
        target_words = self._to_int(value)
        if target_words is not None:
            return target_words
        if not isinstance(value, str):
            return None
        numbers = [int(item) for item in re.findall(r"\d+", value)]
        if len(numbers) >= 2:
            return sum(numbers[:2]) // 2
        if numbers:
            return numbers[0]
        return None

    def resolve_volume_chapter_range(self, volume_num: int) -> Tuple[int, int]:
        """卷章号区间：book_plan > volume_event_plan > legacy chapters_per_volume。"""
        book_range = self.get_book_planner().get_volume_chapter_range(volume_num)
        if book_range:
            return book_range

        event_plan = self.get_event_planner().load_volume_event_plan(volume_num)
        if event_plan and event_plan.get("chapter_range"):
            cr = event_plan["chapter_range"]
            start = self._to_int(cr.get("start"))
            end = self._to_int(cr.get("end"))
            if start is not None and end is not None:
                return start, end

        config = self.load_config()
        cpv = int(config.get("chapters_per_volume") or 50)
        start = (int(volume_num) - 1) * cpv + 1
        return start, int(volume_num) * cpv

    def resolve_current_volume(self, chapter_num: int) -> int:
        """根据章号解析卷号（支持全书规划 / 事件规划 / legacy）。"""
        book_vol = self.get_book_planner().find_volume_for_chapter(chapter_num)
        if book_vol:
            return book_vol

        planning_dir = self.layout.planning_dir
        if planning_dir.exists():
            for plan_path in sorted(planning_dir.glob("volume_*/volume_event_plan.json")):
                if not plan_path.exists():
                    continue
                plan = self._load_json_at(plan_path, {})
                cr = plan.get("chapter_range") or {}
                start = self._to_int(cr.get("start"))
                end = self._to_int(cr.get("end"))
                if start is not None and end is not None and start <= chapter_num <= end:
                    return int(plan.get("volume") or 1)

        config = self.load_config()
        explicit = self._to_int(config.get("current_volume"))
        if explicit and not self.get_book_planner().has_book_plan():
            cpv = int(config.get("chapters_per_volume") or 50)
            legacy_vol = (chapter_num - 1) // cpv + 1
            if legacy_vol == explicit:
                return explicit
        return self._get_current_volume_legacy(config, chapter_num)

    def _get_current_volume_legacy(self, config: Dict[str, Any], chapter_num: int) -> int:
        chapters_per_volume = int(config.get("chapters_per_volume") or 50)
        return max(1, (chapter_num - 1) // chapters_per_volume + 1)

    def _get_current_volume(self, config: Dict[str, Any], chapter_num: int) -> int:
        """根据章节号确定当前卷号（v3：优先全书/事件规划）。"""
        return self.resolve_current_volume(chapter_num)

    def check_volume_completion(self, chapter_num: int) -> Dict[str, Any]:
        """检查当前卷是否完成（联动 book_plan / volume_event_plan / legacy）。"""
        config = self.load_config()
        current_volume = self.resolve_current_volume(chapter_num)
        volume_start, volume_end = self.resolve_volume_chapter_range(current_volume)
        volume_progress_key = f"volume_{current_volume}_progress"
        volume_progress = config.get(volume_progress_key, {})
        completed_in_volume = self._to_int(volume_progress.get("completed_chapters")) or 0

        event_plan = self.get_event_planner().load_volume_event_plan(current_volume)
        events_summary = self._summarize_volume_events(event_plan)

        is_complete = chapter_num >= volume_end or completed_in_volume >= (volume_end - volume_start + 1)
        if events_summary.get("total") and events_summary.get("incomplete"):
            is_complete = is_complete and events_summary["incomplete"] == 0

        next_volume = current_volume + 1 if is_complete else current_volume
        book_meta = self.get_book_planner().get_volume_meta(next_volume) if is_complete else None
        total_volumes = int(merge_event_config(config).get("total_volumes") or 5)
        can_advance = is_complete and current_volume < total_volumes

        return {
            "current_volume": current_volume,
            "volume_start_chapter": volume_start,
            "volume_end_chapter": volume_end,
            "is_complete": is_complete,
            "completed_chapters": completed_in_volume,
            "total_chapters_in_volume": volume_end - volume_start + 1,
            "next_volume": next_volume if can_advance else current_volume,
            "should_transition": can_advance and chapter_num >= volume_end,
            "events_summary": events_summary,
            "next_volume_meta": book_meta,
            "resolution_source": self._volume_resolution_source(current_volume),
        }

    def _volume_resolution_source(self, volume_num: int) -> str:
        if self.get_book_planner().get_volume_chapter_range(volume_num):
            return "book_volume_plan"
        if self.get_event_planner().load_volume_event_plan(volume_num):
            return "volume_event_plan"
        return "legacy_chapters_per_volume"

    def _summarize_volume_events(self, event_plan: Dict[str, Any]) -> Dict[str, Any]:
        events = event_plan.get("events") or []
        if not events:
            return {"total": 0, "incomplete": 0, "statuses": {}}
        incomplete = sum(
            1 for e in events if str(e.get("status", "planned")) not in ("beats_ready", "writing", "complete")
        )
        statuses: Dict[str, int] = {}
        for e in events:
            st = str(e.get("status", "planned"))
            statuses[st] = statuses.get(st, 0) + 1
        return {"total": len(events), "incomplete": incomplete, "statuses": statuses}

    def transition_to_next_volume(self, current_volume: int) -> Dict[str, Any]:
        """流转到下一卷，联动全书规划与事件层。"""
        config = self.load_config()
        next_volume = current_volume + 1
        total_volumes = int(merge_event_config(config).get("total_volumes") or 5)
        if next_volume > total_volumes:
            return {
                "previous_volume": current_volume,
                "current_volume": current_volume,
                "message": f"已是第 {current_volume} 卷（全书共 {total_volumes} 卷），无需流转。",
                "at_book_end": True,
            }

        next_start, next_end = self.resolve_volume_chapter_range(next_volume)
        next_volume_key = f"volume_{next_volume}_progress"
        if next_volume_key not in config:
            config[next_volume_key] = {
                "completed_chapters": 0,
                "volume_start_chapter": next_start,
                "volume_end_chapter": next_end,
            }
        else:
            config[next_volume_key]["volume_start_chapter"] = next_start
            config[next_volume_key]["volume_end_chapter"] = next_end

        config["current_volume"] = next_volume
        config["previous_volume"] = current_volume
        self._set_numeric_field(config, "current_chapter", next_start)

        progress = self.load_progress()
        self._set_numeric_field(progress, "current_chapter", next_start)
        self.save_progress(progress)
        self.save_config(config)

        book_planner = self.get_book_planner()
        next_meta = book_planner.get_volume_meta(next_volume)
        checklist = book_planner.get_transition_checklist(current_volume, next_volume)
        next_event_plan_exists = self.layout.volume_event_plan_path(next_volume).exists()

        return {
            "previous_volume": current_volume,
            "current_volume": next_volume,
            "next_chapter_start": next_start,
            "next_chapter_end": next_end,
            "next_volume_meta": next_meta,
            "checklist": checklist,
            "next_volume_event_plan_exists": next_event_plan_exists,
            "message": f"已流转至第 {next_volume} 卷（第 {next_start} 章起）",
        }

    def build_volume_checkpoint(self, chapter_num: int) -> Dict[str, Any]:
        """卷结检查点（章号区间来自全书/事件规划）。"""
        config = self.load_config()
        current_volume = self.resolve_current_volume(chapter_num)
        volume_start, volume_end = self.resolve_volume_chapter_range(current_volume)
        is_volume_end = chapter_num >= volume_end

        items = [
            {"name": "本卷剧情收束", "required": True},
            {"name": "卷末大钩子确认", "required": True},
            {"name": "角色状态归档", "required": True},
            {"name": "下一卷铺垫检查", "required": True},
        ]
        if self.get_event_planner().uses_event_planning(current_volume):
            items.append({"name": "本卷全部事件 status ≥ beats_ready", "required": True})

        return {
            "due": is_volume_end,
            "volume": current_volume,
            "volume_start_chapter": volume_start,
            "volume_end_chapter": volume_end,
            "is_volume_end": is_volume_end,
            "items": items,
            "transition_ready": is_volume_end,
        }

    # ==================== 角色卡管理 ====================

    def load_character_cards(self) -> Dict[str, Any]:
        """加载角色卡数据"""
        path = self.layout.resolve_config("character_cards")
        default = {"characters": {}, "relationships": {}, "factions": {}}
        return self._load_json_at(path, default) if path else deepcopy(default)

    def save_character_cards(self, character_cards: Dict[str, Any]) -> None:
        """保存角色卡数据"""
        self._save_json("character_cards.json", character_cards)

    def get_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """获取单个角色信息"""
        cards = self.load_character_cards()
        return cards.get("characters", {}).get(character_id)

    def update_character(
        self,
        character_id: str,
        updates: Dict[str, Any],
        chapter_num: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        更新角色信息
        自动记录角色成长历史
        """
        character_cards = self.load_character_cards()
        characters = character_cards.setdefault("characters", {})
        
        if character_id not in characters:
            # 新建角色
            characters[character_id] = {
                "id": character_id,
                "name": updates.get("name", character_id),
                "created_at": chapter_num,
                "history": [],
                "current_status": {},
            }
        
        character = characters[character_id]
        
        # 记录历史变更
        if chapter_num is not None:
            history_entry = {
                "chapter": chapter_num,
                "timestamp": self._get_timestamp(),
                "changes": {},
            }
            for key, value in updates.items():
                if key not in ["id", "name", "created_at", "history"]:
                    old_value = character.get("current_status", {}).get(key)
                    if old_value != value:
                        history_entry["changes"][key] = {
                            "from": old_value,
                            "to": value,
                        }
            
            if history_entry["changes"]:
                character.setdefault("history", []).append(history_entry)
        
        # 更新当前状态
        current_status = character.setdefault("current_status", {})
        for key, value in updates.items():
            if key not in ["id", "name", "created_at", "history"]:
                current_status[key] = value
        
        # 更新基本信息
        if "name" in updates:
            character["name"] = updates["name"]
        
        self.save_character_cards(character_cards)
        return deepcopy(character)

    def sync_characters_from_chapter(
        self,
        chapter_num: int,
        character_updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        从章节元数据同步角色信息
        在 finalize_chapter 时调用
        """
        results = {"updated": [], "created": [], "errors": []}
        
        for char_id, char_data in character_updates.items():
            try:
                is_new = self.get_character(char_id) is None
                updated = self.update_character(char_id, char_data, chapter_num)
                if is_new:
                    results["created"].append(char_id)
                else:
                    results["updated"].append(char_id)
            except Exception as e:
                results["errors"].append({"character": char_id, "error": str(e)})
        
        return results

    def validate_character_consistency(self, chapter_num: int) -> Dict[str, Any]:
        """
        验证角色一致性
        检查角色状态是否符合剧情发展
        """
        character_cards = self.load_character_cards()
        progress = self.load_progress()
        config = self.load_config()
        
        issues = []
        warnings = []
        
        characters = character_cards.get("characters", {})
        
        for char_id, char_data in characters.items():
            current_status = char_data.get("current_status", {})
            history = char_data.get("history", [])
            
            # 检查是否有角色状态记录
            if not history:
                warnings.append(f"角色 {char_id} 没有成长历史记录")
            
            # 检查角色状态是否最新
            last_update = history[-1] if history else None
            if last_update and last_update.get("chapter", 0) < chapter_num - 10:
                warnings.append(f"角色 {char_id} 已有 {chapter_num - last_update['chapter']} 章未更新状态")
            
            # 检查必需字段
            if "power_level" in current_status and "power_system" in config:
                power_level = current_status.get("power_level")
                max_level = config.get("power_system", {}).get("max_level")
                if max_level and power_level and power_level > max_level:
                    issues.append(f"角色 {char_id} 战力等级 {power_level} 超过系统上限 {max_level}")
        
        return {
            "valid": not issues,
            "issues": issues,
            "warnings": warnings,
            "character_count": len(characters),
        }

    def get_character_progress_summary(self) -> Dict[str, Any]:
        """获取角色进度摘要"""
        character_cards = self.load_character_cards()
        characters = character_cards.get("characters", {})
        
        summary = {
            "total_characters": len(characters),
            "protagonist": None,
            "key_characters": [],
            "recent_updates": [],
        }
        
        for char_id, char_data in characters.items():
            # 识别主角（标记为 protagonist 或有最多历史记录）
            if char_data.get("current_status", {}).get("is_protagonist"):
                summary["protagonist"] = {
                    "id": char_id,
                    "name": char_data.get("name"),
                    "current_status": char_data.get("current_status", {}),
                }
            
            # 关键角色（有重要标记或频繁更新）
            history = char_data.get("history", [])
            if len(history) > 5:
                summary["key_characters"].append({
                    "id": char_id,
                    "name": char_data.get("name"),
                    "update_count": len(history),
                })
            
            # 最近更新
            if history:
                last_update = history[-1]
                summary["recent_updates"].append({
                    "character": char_id,
                    "chapter": last_update.get("chapter"),
                    "changes": list(last_update.get("changes", {}).keys()),
                })
        
        # 按章节排序最近更新
        summary["recent_updates"].sort(key=lambda x: x.get("chapter", 0), reverse=True)
        summary["recent_updates"] = summary["recent_updates"][:5]  # 只保留最近5条
        
        return summary

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
