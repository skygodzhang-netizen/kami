"""
Writing Loop - Manages the chapter generation process (v2.1)
"""
from typing import Any, Dict

try:
    from .prompt_utils import format_blocked_message
    from .project_state import ProjectState
except ImportError:
    from prompt_utils import format_blocked_message
    from project_state import ProjectState


class WritingLoop:
    def __init__(self, phase_runner):
        self.phase_runner = phase_runner

    def write_chapter(self, chapter_num, **kwargs):
        stage = str(kwargs.get("stage") or "outline").strip().lower()
        batch_mode = bool(kwargs.get("batch_mode", False))
        chapter_word_count = int(kwargs.get("chapter_word_count", 2500))
        preparation = self.phase_runner.run_phase("prepare", chapter_num=chapter_num, **kwargs)
        preflight = preparation["preflight"]

        if not preflight["ready"]:
            return {
                "status": "blocked",
                "message": format_blocked_message(
                    preflight.get("blockers", []),
                    [
                        "运行 workflow_audit 查看缺失文件",
                        "若 JSON 损坏，用 Python json.dump 重建 config/ 下对应文件",
                    ],
                ),
                "data": {"preflight": preflight},
            }

        workflow_gate = self.phase_runner.config_manager.validate_chapter_workflow(
            chapter_num=chapter_num,
            target_phase=stage,
        )

        if stage == "draft" and batch_mode and not workflow_gate["ready"]:
            workflow_gate = self._apply_batch_mode_outline_gate(
                chapter_num=chapter_num,
                workflow_gate=workflow_gate,
                preparation=preparation,
            )

        if not workflow_gate["ready"]:
            return {
                "status": "blocked",
                "message": format_blocked_message(
                    workflow_gate.get("blockers", []),
                    [
                        "完成 confirm_step(step='outline') 后再写正文",
                        "或显式传入 batch_mode=True（须用户授权跳过大纲确认）",
                    ],
                ),
                "data": {"preflight": preflight, "workflow": workflow_gate},
            }

        if stage not in {"outline", "draft"}:
            return {
                "status": "error",
                "message": f"不支持的章节阶段：{stage}",
                "data": {"preflight": preflight, "workflow": workflow_gate},
            }

        if stage == "outline":
            project_state = ProjectState(str(self.phase_runner.config_manager.run_dir))
            project_state.trigger("before_outline", chapter_num=chapter_num)
            outline = self.phase_runner.run_phase(
                "outline",
                chapter_num=chapter_num,
                chapter_word_count=chapter_word_count,
                context=preparation["context"],
                input_data=preparation["input"],
            )
            chapter_workflow = self.phase_runner.config_manager.record_generated_outline(
                chapter_num=chapter_num,
                outline=outline["content"],
                prompt=outline["prompt"],
                requested_word_count=chapter_word_count,
                word_limits=outline.get("word_limits"),
            )
            return {
                "status": "awaiting_confirmation",
                "message": "章纲生成完毕，请确认后再生成正文。",
                "data": {
                    "preflight": preflight,
                    "outline": outline["content"],
                    "outline_prompt": outline["prompt"],
                    "word_limits": outline.get("word_limits"),
                    "workflow": chapter_workflow,
                },
            }

        confirmed_outline = (
            kwargs.get("confirmed_outline")
            or workflow_gate["chapter_workflow"].get("outline", {}).get("content", "")
        )
        if not confirmed_outline:
            confirmed_outline = self._synthetic_outline_from_plot_engine(preparation)
        if not confirmed_outline:
            return {
                "status": "blocked",
                "message": format_blocked_message(
                    ["缺少已确认的单章大纲，无法生成正文。"],
                    ["先 write_chapter(stage='outline') 并 confirm_step(step='outline')"],
                ),
                "data": {"preflight": preflight, "workflow": workflow_gate},
            }

        draft = self.phase_runner.run_phase(
            "draft",
            chapter_num=chapter_num,
            chapter_hook=confirmed_outline,
            chapter_word_count=chapter_word_count,
            context=preparation["context"],
            input_data=preparation["input"],
        )

        validation = self.phase_runner.run_phase(
            "style_check",
            draft=draft["content"],
            context=preparation["context"],
            voice_config=preparation["input"].get("voice_config"),
        )

        chapter_workflow = self.phase_runner.config_manager.record_generated_draft(
            chapter_num=chapter_num,
            draft=draft["content"],
            prompt=draft["prompt"],
            word_report=draft["word_report"],
            validation=validation,
        )
        ProjectState(str(self.phase_runner.config_manager.run_dir)).trigger(
            "after_draft",
            chapter_num=chapter_num,
            content=draft["content"],
            validation=validation,
        )

        data: Dict[str, Any] = {
            "preflight": preflight,
            "outline": confirmed_outline,
            "draft": draft["content"],
            "draft_prompt": draft["prompt"],
            "word_count": {
                "target": chapter_word_count,
                "chinese_characters": draft["word_count"],
                "report": draft["word_report"],
                "limits": draft.get("word_limits"),
            },
            "validation": validation,
            "workflow": chapter_workflow,
            "batch_mode": batch_mode,
        }

        if validation.get("critical_issues"):
            return {
                "status": "needs_revision",
                "message": format_blocked_message(
                    [item.get("message", "") for item in validation["critical_issues"]],
                    ["修正后重新 confirm_step(step='draft') 或重新 generate draft"],
                ),
                "data": data,
            }

        return {
            "status": "awaiting_confirmation",
            "message": f"第 {chapter_num} 章正文生成完毕，请确认后再终稿入库。",
            "data": data,
        }

    def _apply_batch_mode_outline_gate(
        self,
        chapter_num: int,
        workflow_gate: Dict[str, Any],
        preparation: Dict[str, Any],
    ) -> Dict[str, Any]:
        cm = self.phase_runner.config_manager
        chapter_state = workflow_gate.get("chapter_workflow", {})
        outline_state = chapter_state.get("outline", {})
        if outline_state.get("status") == "generated" and outline_state.get("content"):
            cm.confirm_outline(chapter_num=chapter_num, outline_text=outline_state["content"])
            return cm.validate_chapter_workflow(chapter_num=chapter_num, target_phase="draft")

        synthetic = self._synthetic_outline_from_plot_engine(preparation)
        if synthetic:
            cm.record_generated_outline(
                chapter_num=chapter_num,
                outline=synthetic,
                prompt="[batch_mode synthetic outline from plot_engine]",
                requested_word_count=int(preparation["input"].get("chapter_word_count", 2500)),
            )
            cm.confirm_outline(chapter_num=chapter_num, outline_text=synthetic)
            return cm.validate_chapter_workflow(chapter_num=chapter_num, target_phase="draft")
        return workflow_gate

    def _synthetic_outline_from_plot_engine(self, preparation: Dict[str, Any]) -> str:
        plot_engine = (
            preparation["input"].get("plot_engine_result")
            or preparation["context"].get("plot_engine")
            or ""
        ).strip()
        if not plot_engine:
            return ""
        progress = preparation["input"].get("progress_node") or preparation["context"].get("progress_node") or ""
        return (
            f"### 【章节标题】\n批量模式合成大纲\n\n"
            f"### 【核心钩子】\n基于剧情推演结果执行\n\n"
            f"### 【关键场景】\n{plot_engine[:2000]}\n\n"
            f"### 【结尾钩子】\n承接剧情推演末尾钩子\n\n"
            f"<!-- progress_node: {progress[:500]} -->"
        )
