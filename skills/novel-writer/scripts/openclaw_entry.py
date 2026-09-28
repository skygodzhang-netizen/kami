"""
Novel Writer - OpenClaw Skill Entry Point (v3.0.0)
"""
import json
import re
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from .config_manager import ConfigManager
    from .phase_runner import PhaseRunner
    from .style_validator import StyleValidator, build_word_report, count_text_units
    from .writing_loop import WritingLoop
    from .plot_workshop import PlotWorkshop
    from .relationship_manager import RelationshipManager
    from .relationship_validator import RelationshipValidator
    from .plot_recommender import PlotRecommender
    from .project_state import ProjectState
    from .prompt_utils import build_task_prompt, format_blocked_message, serialize_character_cards
    from .event_planning import EventPlanner, merge_event_config, extract_json_from_llm
    from .book_planning import BookPlanner
except ImportError:
    from config_manager import ConfigManager
    from phase_runner import PhaseRunner
    from style_validator import StyleValidator, build_word_report, count_text_units
    from writing_loop import WritingLoop
    from plot_workshop import PlotWorkshop
    from relationship_manager import RelationshipManager
    from relationship_validator import RelationshipValidator
    from plot_recommender import PlotRecommender
    from project_state import ProjectState
    from prompt_utils import build_task_prompt, format_blocked_message, serialize_character_cards
    from event_planning import EventPlanner, merge_event_config, extract_json_from_llm
    from book_planning import BookPlanner

SKILL_VERSION = "3.0.0"


def _resolve_genre(config_manager: ConfigManager, genre: Optional[str], kwargs: Dict[str, Any]) -> str:
    return config_manager.resolve_genre(genre, kwargs=kwargs)


def _resolve_core_pleasure(
    config_manager: ConfigManager,
    core_pleasure: Optional[str],
    kwargs: Dict[str, Any],
) -> str:
    return config_manager.resolve_core_pleasure(core_pleasure, kwargs=kwargs)


def _count_net_text_units(text: str) -> int:
    return count_text_units(text)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    os.replace(temp_path, path)


def _save_text_artifact(base_dir: Path, file_name: str, content: str, *, subdir: Optional[str] = None) -> str:
    target_dir = base_dir / subdir if subdir else base_dir
    target_path = target_dir / file_name
    normalized = str(content or "").strip()
    _atomic_write_text(target_path, f"{normalized}\n" if normalized else "")
    return str(target_path)


def _extract_json_payload(raw_text: str) -> Dict[str, Any]:
    if not raw_text or not raw_text.strip():
        raise ValueError("声音配置为空，无法解析为 JSON")

    candidate = raw_text.strip()
    fenced_match = re.search(r"```json\s*(.*?)\s*```", candidate, flags=re.S | re.I)
    if fenced_match:
        candidate = fenced_match.group(1).strip()
    elif candidate.startswith("```") and candidate.endswith("```"):
        candidate = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", candidate, flags=re.S).strip()

    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("声音配置必须是 JSON 对象")
    return parsed


def _build_chapter_beats_file_name(start_chapter: int, content: str) -> str:
    chapter_numbers = [int(item) for item in re.findall(r"第\s*(\d+)\s*章", content or "")]
    if chapter_numbers:
        return f"chapter_beats_{min(chapter_numbers)}-{max(chapter_numbers)}.md"
    return f"chapter_beats_{int(start_chapter)}.md"


def _extract_chapter_title(text: str) -> str:
    if not text:
        return ""
    first_line = str(text).strip().splitlines()[0].strip()
    if len(first_line) <= 40:
        return first_line
    return first_line[:40]


def run_skill(
    book_title: Optional[str] = None,
    genre: Optional[str] = None,
    core_pleasure: Optional[str] = None,  # 新增：核心爽感类型
    target_words: int = 1000000,
    workspace_root: Optional[str] = None,
    run_dir: Optional[str] = None,
    mode: str = "manual",
    oc_context: Optional[Dict[str, Any]] = None,
    action: str = "init",
    **kwargs
) -> Dict[str, Any]:
    """
    Main entry point for OpenClaw to call this skill.
    适配新Prompt系统：
    - world_hooks (保留)
    - voice_config (原style)
    - volume_arc (原volume)
    - chapter_beats (保留)
    - plot_engine (保留)
    - write_chapter (保留)
    """
    results = {
        "status": "pending",
        "action": action,
        "message": "",
        "data": {}
    }
    
    if run_dir:
        base_dir = Path(run_dir)
    elif workspace_root:
        base_dir = Path(workspace_root)
    else:
        base_dir = Path.home() / ".openclaw" / "novel-writer"
    base_dir.mkdir(parents=True, exist_ok=True)

    # 初始化关系管理器（v1.4.0）
    relationship_manager = RelationshipManager(base_dir)
    relationship_validator = RelationshipValidator(relationship_manager)
    plot_recommender = PlotRecommender(relationship_manager, relationship_validator)
    plot_workshop = PlotWorkshop()

    def call_model(prompt: str, **model_kwargs) -> str:
        if oc_context and hasattr(oc_context, "model_call"):
            return oc_context.model_call(prompt, **model_kwargs)
        if oc_context and "model_callable" in oc_context:
            return oc_context["model_callable"](prompt, **model_kwargs)
        if oc_context and "generate" in oc_context:
            return oc_context["generate"](prompt, **model_kwargs)
        raise RuntimeError(
            "模型未配置：请在 oc_context 中提供 model_call / model_callable / generate。"
        )

    prompts_dir = Path(__file__).parent.parent / "prompts"
    _model_configured = bool(
        oc_context
        and (
            hasattr(oc_context, "model_call")
            or (isinstance(oc_context, dict) and ("model_callable" in oc_context or "generate" in oc_context))
        )
    )

    def load_prompt(name: str) -> str:
        with open(prompts_dir / f"{name}.md", "r", encoding="utf-8") as f:
            return f.read()

    try:
        config_manager = ConfigManager(base_dir)
        config_manager.layout.ensure_dirs()
        phase_runner = PhaseRunner(
            config_manager=config_manager,
            prompt_loader=load_prompt,
            model_caller=call_model,
            word_counter=_count_net_text_units,
            prompts_dir=prompts_dir,
        )
        writing_loop = WritingLoop(phase_runner)
        project_state = ProjectState(str(base_dir))
        genre = _resolve_genre(config_manager, genre, kwargs)
        core_pleasure = _resolve_core_pleasure(config_manager, core_pleasure, kwargs)
        
        if not _model_configured and action not in {
            "workflow_audit",
            "plan_volume_events",
            "plan_event",
            "plan_book_volumes",
            "plot_workshop",
            "get_character",
            "list_characters",
            "list_relationships",
            "get_relationship",
            "get_faction",
            "list_factions",
            "get_relationship_network",
            "validate_relationships",
            "detect_conflicts",
            "validate_characters",
            "check_volume_completion",
            "transition_volume",
        }:
            results["status"] = "error"
            results["message"] = "模型未配置，无法执行需要 LLM 的 action。请在 oc_context 中注入 model_callable。"
            return results
        
        # 弹性字数：新配置2000-5000，默认2500
        chapter_word_count = int(kwargs.get("chapter_word_count", 2500))
        
        if action == "init":
            pre_init_gate = config_manager.validate_pre_init_gate(force=bool(kwargs.get("force")))
            if not pre_init_gate["ready"]:
                results["status"] = "blocked"
                results["message"] = format_blocked_message(
                    pre_init_gate["blockers"],
                    [
                        "全新项目先完成 Pre-Init 四阶段并 confirm_pre_init",
                        "续写已有项目可 init(force=True)",
                    ],
                )
                results["data"] = pre_init_gate
                return results

            config = config_manager.load_config()
            event_defaults = merge_event_config(config)
            config.update(
                {
                    "book_title": book_title or config.get("book_title", ""),
                    "genre": genre or config.get("genre", ""),
                    "target_words": int(target_words),
                    "current_chapter": int(config.get("current_chapter", 1) or 1),
                    "current_volume": int(config.get("current_volume", 1) or 1),
                    "skill_version": SKILL_VERSION,
                }
            )
            for key, value in event_defaults.items():
                config.setdefault(key, value)
            config_manager.save_config(config)

            progress = config_manager.load_progress()
            progress.setdefault("current_chapter", 1)
            progress.setdefault("current_chapters", 0)
            progress.setdefault("current_words", 0)
            progress.setdefault("target_words", int(target_words))
            config_manager.save_progress(progress)

            # 初始化标准配置文件占位
            if not config_manager.layout.resolve_config("character_cards"):
                config_manager.save_character_cards(
                    {"characters": {}, "relationships": {}, "factions": {}}
                )
            if not config_manager.layout.resolve_config("workflow_state"):
                config_manager.save_workflow_state({"chapters": {}})

            author_profile = config_manager.ensure_author_profile()

            results["message"] = f"Novel Writer v{SKILL_VERSION} 初始化完成。可继续 world_hooks。"
            results["status"] = "awaiting_confirmation"
            results["data"] = {
                "config_path": str(config_manager.layout.config_path("novel_writer_config")),
                "progress_path": str(config_manager.layout.config_path("progress")),
                "author_profile_path": str(config_manager.layout.config_path("author_profile")),
                "layout": {
                    "config_dir": str(config_manager.layout.config_dir),
                    "plot_engine_dir": str(config_manager.layout.plot_engine_dir),
                },
                "author_profile": author_profile,
            }

        elif action == "confirm_pre_init":
            creative = config_manager.mark_pre_init_complete(notes=kwargs.get("notes"))
            results["status"] = "complete"
            results["message"] = "Pre-Init 已完成，可执行 init。"
            results["data"] = {"creative_workflow": creative}

        elif action == "world_hooks":
            template = load_prompt("world_hooks")
            prompt = build_task_prompt(
                template,
                {
                    "genre": genre,
                    "core_pleasure": core_pleasure,
                },
                prompts_dir=prompts_dir,
                user_data_keys={"genre", "core_pleasure"},
            )

            response = call_model(prompt)
            results["data"]["world_hooks"] = response
            results["data"]["world_hooks_path"] = _save_text_artifact(base_dir, "world_hooks.md", response)
            results["message"] = "世界观爽点预埋完毕，请确认。"
            results["status"] = "awaiting_confirmation"

        elif action == "voice_config":
            template = load_prompt("voice_config")
            world_hooks = kwargs.get("world_hooks", "")
            author_profile = config_manager.load_author_profile()
            fusion_path = Path(__file__).parent.parent / "fusion-writer-template.json"
            fusion_style = ""
            if fusion_path.exists():
                with open(fusion_path, "r", encoding="utf-8") as f:
                    fusion_style = f.read()
            prompt = build_task_prompt(
                template,
                {
                    "genre": genre,
                    "world_atmosphere": kwargs.get("world_atmosphere", "热血"),
                    "protagonist_personality": kwargs.get(
                        "protagonist_personality", kwargs.get("protagonist", "坚韧")
                    ),
                    "target_platform": kwargs.get("target_platform", "起点"),
                    "world_hooks": world_hooks,
                    "base_voice_config": fusion_style[:2000] if fusion_style else "",
                    "world_hooks_full": world_hooks,
                    "world_hooks_brief": world_hooks[:500] if len(world_hooks) > 500 else world_hooks,
                    "protagonist_sheet": kwargs.get("protagonist_sheet", ""),
                    "novel_genre": genre,
                    "author_profile": json.dumps(author_profile, ensure_ascii=False, indent=2),
                    "author_signature": json.dumps(
                        author_profile.get("author_signature", {}), ensure_ascii=False, indent=2
                    ),
                    "mature_content_policy": json.dumps(
                        author_profile.get("mature_content_policy", {}), ensure_ascii=False, indent=2
                    ),
                },
                prompts_dir=prompts_dir,
                user_data_keys={
                    "world_hooks",
                    "world_hooks_full",
                    "world_hooks_brief",
                    "protagonist_sheet",
                    "base_voice_config",
                    "author_profile",
                    "author_signature",
                    "mature_content_policy",
                },
                user_data_limits={"world_hooks_full": 12000, "world_hooks": 8000},
            )

            response = call_model(prompt)
            voice_config_payload = config_manager.normalize_voice_config(
                config_manager.merge_author_profile_into_voice_config(_extract_json_payload(response))
            )
            voice_config_validation = config_manager.validate_voice_config(voice_config_payload)
            if not voice_config_validation["valid"]:
                results["status"] = "error"
                results["message"] = "声音配置生成失败，JSON 结构不符合要求。"
                results["data"] = {
                    "errors": voice_config_validation["errors"],
                    "warnings": voice_config_validation["warnings"],
                }
                return results
            voice_config_path = config_manager.layout.config_path("voice_config")
            _atomic_write_text(
                voice_config_path,
                f"{json.dumps(voice_config_payload, ensure_ascii=False, indent=2)}\n",
            )
            results["data"]["voice_config"] = voice_config_payload
            results["data"]["voice_config_path"] = str(voice_config_path)
            results["data"]["validation"] = voice_config_validation
            results["message"] = "声音配置定制完毕，请确认。"
            results["status"] = "awaiting_confirmation"

        elif action == "plan_book_volumes":
            book_planner = config_manager.get_book_planner()
            config = config_manager.load_config()
            event_cfg = config_manager.get_event_config()
            tw = int(kwargs.get("target_words") or target_words or config.get("target_words") or 1_000_000)
            total_vols = int(kwargs.get("total_volumes") or event_cfg.get("total_volumes") or 5)
            title = str(book_title or config.get("book_title") or "")
            world_hooks_text = kwargs.get("world_hooks") or config_manager.read_text(
                config_manager.find_file(["world_hooks.md"])
            )
            cpv = event_cfg.get("chapters_per_volume")
            cpv_hint = str(cpv) if cpv else "按卷弧与事件层弹性分配"

            md_stub, json_stub = book_planner.generate_rule_stub(
                target_words=tw,
                total_volumes=total_vols,
                book_title=title,
            )
            use_llm = bool(kwargs.get("use_llm", _model_configured)) and _model_configured

            if use_llm:
                template = load_prompt("book_volume_plan")
                prompt = build_task_prompt(
                    template,
                    {
                        "book_title": title,
                        "genre": str(genre or config.get("genre") or "未指定"),
                        "target_words": str(tw),
                        "total_volumes": str(total_vols),
                        "chapters_per_volume_hint": cpv_hint,
                        "world_hooks": world_hooks_text,
                    },
                    prompts_dir=prompts_dir,
                    user_data_keys={"world_hooks"},
                )
                response = call_model(prompt)
                md_text, plan_json = book_planner.merge_llm_response(
                    response,
                    target_words=tw,
                    total_volumes=total_vols,
                    book_title=title,
                    fallback=json_stub,
                )
            else:
                md_text, plan_json = md_stub, json_stub

            paths = book_planner.save_plan(md_text, plan_json)
            config["total_volumes"] = int(plan_json.get("total_volumes") or total_vols)
            config["target_words"] = int(plan_json.get("target_words") or tw)
            config["book_title"] = plan_json.get("book_title") or title
            config_manager.save_config(config)

            results["data"] = {
                "book_volume_plan": md_text,
                "book_volume_plan_json": plan_json,
                **paths,
                "volume_count": len(plan_json.get("volumes", [])),
                "source": plan_json.get("source", "rule_stub"),
            }
            results["message"] = (
                f"全书 {plan_json.get('total_volumes')} 卷规划已落盘"
                f"（{len(plan_json.get('volumes', []))} 卷明细）。"
                "可进入第 1 卷 volume_arc → plan_volume_events。"
            )
            results["status"] = "awaiting_confirmation"

        elif action == "volume_arc":
            template = load_prompt("volume_arc")
            prompt = build_task_prompt(
                template,
                {
                    "world_hooks": kwargs.get("world_hooks", ""),
                    "target_word_count": str(target_words),
                    "chapter_word_count": str(chapter_word_count),
                },
                prompts_dir=prompts_dir,
                user_data_keys={"world_hooks"},
            )

            response = call_model(prompt)
            results["data"]["volume_arc"] = response
            results["data"]["volume_arc_path"] = _save_text_artifact(base_dir, "volume_arc.md", response)
            results["message"] = "卷情绪弧设计完毕，请确认。"
            results["status"] = "awaiting_confirmation"

        elif action == "plan_volume_events":
            volume_num = int(kwargs.get("volume_num") or config_manager.load_config().get("current_volume", 1))
            planner = config_manager.get_event_planner()
            config = config_manager.load_config()
            event_cfg = config_manager.get_event_config()
            volume_arc = kwargs.get("volume_arc") or config_manager.read_text(
                config_manager.find_file(["volume_*_outline.md", "volume_arc.md"])
            )
            world_hooks = kwargs.get("world_hooks") or config_manager.read_text(
                config_manager.find_file(["world_hooks.md"])
            )
            pipeline = bool(kwargs.get("pipeline") or kwargs.get("use_engine"))
            event_count = kwargs.get("event_count") or event_cfg.get("events_per_volume_default")

            workshop = plot_workshop.generate_volume_workshop(
                volume_num,
                volume_arc=volume_arc,
                world_hooks=world_hooks,
                event_count=int(event_count),
                event_chapters_min=int(event_cfg.get("event_chapters_min") or 3),
                event_chapters_max=int(event_cfg.get("event_chapters_max") or 15),
                genre=genre or config.get("genre"),
                core_pleasure=core_pleasure or kwargs.get("core_pleasure"),
            )
            ws_path = config_manager.layout.plot_workshop_volume_path(volume_num)
            _atomic_write_text(ws_path, f"{json.dumps(workshop, ensure_ascii=False, indent=2)}\n")
            results["data"]["workshop_volume"] = workshop
            results["data"]["workshop_volume_path"] = str(ws_path)

            if pipeline and _model_configured:
                ws_template = load_prompt("plot_workshop_volume")
                ws_prompt = build_task_prompt(
                    ws_template,
                    {
                        "volume_num": str(volume_num),
                        "volume_arc": volume_arc,
                        "world_hooks": world_hooks,
                        "event_chapters_min": str(event_cfg.get("event_chapters_min")),
                        "event_chapters_max": str(event_cfg.get("event_chapters_max")),
                        "events_per_volume": str(event_count),
                        "workshop_volume_stub": workshop,
                    },
                    prompts_dir=prompts_dir,
                    user_data_keys={"volume_arc", "world_hooks", "workshop_volume_stub"},
                )
                try:
                    ws_llm = call_model(ws_prompt)
                    workshop = {**workshop, **extract_json_from_llm(ws_llm), "source": "llm_refined"}
                    _atomic_write_text(ws_path, f"{json.dumps(workshop, ensure_ascii=False, indent=2)}\n")
                    results["data"]["workshop_volume"] = workshop
                except (ValueError, json.JSONDecodeError):
                    pass

                eng_template = load_prompt("plot_engine_volume")
                eng_prompt = build_task_prompt(
                    eng_template,
                    {
                        "volume_num": str(volume_num),
                        "volume_arc": volume_arc,
                        "world_hooks": world_hooks,
                        "workshop_volume": workshop,
                        "event_chapters_min": str(event_cfg.get("event_chapters_min")),
                        "event_chapters_max": str(event_cfg.get("event_chapters_max")),
                        "chapters_per_volume": str(event_cfg.get("chapters_per_volume") or "无"),
                    },
                    prompts_dir=prompts_dir,
                    user_data_keys={"volume_arc", "world_hooks", "workshop_volume"},
                )
                eng_response = call_model(eng_prompt)
                eng_path = config_manager.layout.plot_engine_volume_path(volume_num)
                _atomic_write_text(eng_path, f"{str(eng_response).strip()}\n")
                result = planner.merge_volume_engine_response(
                    volume_num,
                    eng_response,
                    fallback_workshop=workshop,
                    volume_arc_text=volume_arc,
                )
                results["data"].update(result)
                results["data"]["plot_engine_volume_path"] = str(eng_path)
                results["message"] = (
                    f"第 {volume_num} 卷：工坊+推演 pipeline 完成，{result['event_count']} 个事件已落盘。"
                )
            elif pipeline:
                result = planner.build_plan_from_volume_workshop(
                    volume_num,
                    workshop,
                    volume_title=str(kwargs.get("volume_title") or ""),
                    volume_arc_text=volume_arc,
                    source="workshop_rule",
                )
                results["data"].update(result)
                results["message"] = (
                    f"第 {volume_num} 卷：规则工坊已转事件规划（{result['event_count']} 个事件）。"
                    "配置 LLM 后可 pipeline+use_engine 获得推演扩写。"
                )
            else:
                result = planner.plan_volume_events(
                    volume_num,
                    volume_title=str(kwargs.get("volume_title") or ""),
                    event_count=event_count,
                    volume_arc_text=volume_arc,
                )
                results["data"].update(result)
                results["message"] = (
                    f"第 {volume_num} 卷已生成 {result['event_count']} 个事件卡片（规则桩）。"
                    "推荐 pipeline=True 走工坊主链。"
                )
            results["status"] = "awaiting_confirmation"

        elif action == "plan_event":
            volume_num = int(kwargs.get("volume_num") or config_manager.load_config().get("current_volume", 1))
            event_id = kwargs.get("event_id")
            if not event_id:
                results["status"] = "error"
                results["message"] = "缺少必需参数：event_id"
                return results
            planner = config_manager.get_event_planner()
            config = config_manager.load_config()
            pipeline = bool(kwargs.get("pipeline") or kwargs.get("use_engine"))
            plan = planner.load_volume_event_plan(volume_num)
            event_card = planner.get_event(plan, str(event_id))
            if not event_card:
                results["status"] = "blocked"
                results["message"] = f"事件 {event_id} 不在卷 {volume_num} 规划内，请先 plan_volume_events。"
                return results

            volume_workshop_path = config_manager.layout.plot_workshop_volume_path(volume_num)
            volume_workshop = (
                json.loads(volume_workshop_path.read_text(encoding="utf-8"))
                if volume_workshop_path.exists()
                else {}
            )
            world_hooks = kwargs.get("world_hooks") or config_manager.read_text(
                config_manager.find_file(["world_hooks.md"])
            )
            workshop_event = plot_workshop.generate_event_workshop(
                event_card,
                volume_workshop=volume_workshop,
                world_hooks=world_hooks,
                genre=genre or config.get("genre"),
            )
            we_path = config_manager.layout.plot_workshop_event_path(volume_num, str(event_id))
            _atomic_write_text(we_path, f"{json.dumps(workshop_event, ensure_ascii=False, indent=2)}\n")
            results["data"]["workshop_event"] = workshop_event
            results["data"]["workshop_event_path"] = str(we_path)

            try:
                if pipeline and _model_configured:
                    vol_engine_path = config_manager.layout.plot_engine_volume_path(volume_num)
                    vol_engine_excerpt = (
                        config_manager.read_text(vol_engine_path)[:3000]
                        if vol_engine_path.exists()
                        else ""
                    )
                    character_status = serialize_character_cards(config_manager.load_character_cards())
                    eng_template = load_prompt("plot_engine_event")
                    eng_prompt = build_task_prompt(
                        eng_template,
                        {
                            "volume_num": str(volume_num),
                            "event_id": str(event_id),
                            "event_card": event_card,
                            "workshop_event": workshop_event,
                            "plot_engine_volume_excerpt": vol_engine_excerpt,
                            "character_status": character_status,
                        },
                        prompts_dir=prompts_dir,
                        user_data_keys={
                            "event_card",
                            "workshop_event",
                            "plot_engine_volume_excerpt",
                            "character_status",
                        },
                    )
                    eng_response = call_model(eng_prompt)
                    ee_path = config_manager.layout.plot_engine_event_path(volume_num, str(event_id))
                    _atomic_write_text(ee_path, f"{str(eng_response).strip()}\n")
                    result = planner.save_event_outline_from_engine(
                        volume_num, str(event_id), eng_response
                    )
                    results["data"].update(result)
                    results["data"]["plot_engine_event_path"] = str(ee_path)
                    results["message"] = f"事件 {event_id}：工坊+推演 pipeline 完成，event_outline 已落盘。"
                elif pipeline:
                    result = planner.plan_event(
                        volume_num,
                        str(event_id),
                        extra_notes=json.dumps(workshop_event, ensure_ascii=False, indent=2)[:1200],
                    )
                    results["data"].update(result)
                    results["message"] = (
                        f"事件 {event_id}：规则工坊已转 event_outline。"
                        "配置 LLM 后可用 pipeline=True 获得推演扩写。"
                    )
                else:
                    result = planner.plan_event(
                        volume_num,
                        str(event_id),
                        extra_notes=str(kwargs.get("notes") or ""),
                    )
                    results["data"].update(result)
                    results["message"] = f"事件 {event_id} 纲已生成，可执行 chapter_beats（指定 event_id）。"
            except (FileNotFoundError, ValueError) as exc:
                results["status"] = "blocked"
                results["message"] = str(exc)
                return results
            results["status"] = "awaiting_confirmation"

        elif action == "chapter_beats":
            config = config_manager.load_config()
            volume_num = int(kwargs.get("volume_num") or config.get("current_volume", 1))
            event_id = kwargs.get("event_id")
            planner = config_manager.get_event_planner()
            beats_gate = planner.validate_chapter_beats_gate(volume_num, event_id)
            if not beats_gate["ready"]:
                results["status"] = "blocked"
                results["message"] = format_blocked_message(beats_gate["blockers"])
                results["data"] = beats_gate
                return results

            template = load_prompt("chapter_beats")
            volume_arc = kwargs.get("volume_arc", "")
            if not volume_arc:
                volume_arc = config_manager.read_text(
                    config_manager.find_file(["volume_*_outline.md", "volume_arc.md"])
                )
            start_chapter = int(kwargs.get("start_chapter", 1))
            event = beats_gate.get("event") or {}
            event_outline = config_manager.read_text(
                Path(beats_gate["event_outline_path"]) if beats_gate.get("event_outline_path") else None
            ) if not beats_gate.get("legacy") else kwargs.get("event_outline", "")

            if event and not start_chapter:
                start_chapter = int(event.get("start_chapter") or 1)

            prompt = build_task_prompt(
                template,
                {
                    "volume_emotion_arc": volume_arc,
                    "volume_hook_chain": kwargs.get("volume_hook_chain", ""),
                    "start_chapter": str(start_chapter),
                    "current_volume_arc": volume_arc,
                    "event_id": str(event.get("event_id", event_id or "")),
                    "event_title": str(event.get("title", "")),
                    "event_outline": event_outline,
                    "estimated_chapters": str(event.get("estimated_chapters", "")),
                },
                prompts_dir=prompts_dir,
                user_data_keys={
                    "volume_emotion_arc",
                    "volume_hook_chain",
                    "current_volume_arc",
                    "event_outline",
                },
            )

            response = call_model(prompt)
            results["data"]["chapter_beats"] = response
            beats_path = _save_text_artifact(
                base_dir,
                _build_chapter_beats_file_name(start_chapter, response),
                response,
                subdir="plot_engine",
            )
            results["data"]["chapter_beats_path"] = beats_path
            if event_id and event:
                chapter_numbers = [int(item) for item in re.findall(r"第\s*(\d+)\s*章", response or "")]
                actual = len(chapter_numbers) if chapter_numbers else int(event.get("estimated_chapters") or 0)
                planner.mark_event_beats_ready(volume_num, str(event_id), actual)
                results["data"]["event_id"] = event_id
                results["data"]["volume_num"] = volume_num
            results["message"] = "章节节拍表生成完毕，请确认。"
            results["status"] = "awaiting_confirmation"

        elif action == "plot_engine":
            scope = str(kwargs.get("scope") or "chapter").lower()
            event_cfg = config_manager.get_event_config()
            config = config_manager.load_config()
            volume_num = int(kwargs.get("volume_num") or config.get("current_volume", 1))
            event_id = kwargs.get("event_id")
            planner = config_manager.get_event_planner()

            if scope == "volume":
                volume_arc = kwargs.get("volume_arc") or config_manager.read_text(
                    config_manager.find_file(["volume_*_outline.md", "volume_arc.md"])
                )
                world_hooks = kwargs.get("world_hooks") or config_manager.read_text(
                    config_manager.find_file(["world_hooks.md"])
                )
                ws_path = config_manager.layout.plot_workshop_volume_path(volume_num)
                if ws_path.exists():
                    workshop = json.loads(ws_path.read_text(encoding="utf-8"))
                else:
                    workshop = plot_workshop.generate_volume_workshop(
                        volume_num,
                        volume_arc=volume_arc,
                        world_hooks=world_hooks,
                        event_count=int(event_cfg.get("events_per_volume_default") or 3),
                        event_chapters_min=int(event_cfg.get("event_chapters_min") or 3),
                        event_chapters_max=int(event_cfg.get("event_chapters_max") or 15),
                        genre=genre or config.get("genre"),
                        core_pleasure=core_pleasure,
                    )
                    _atomic_write_text(ws_path, f"{json.dumps(workshop, ensure_ascii=False, indent=2)}\n")

                template = load_prompt("plot_engine_volume")
                prompt = build_task_prompt(
                    template,
                    {
                        "volume_num": str(volume_num),
                        "volume_arc": volume_arc,
                        "world_hooks": world_hooks,
                        "workshop_volume": workshop,
                        "event_chapters_min": str(event_cfg.get("event_chapters_min")),
                        "event_chapters_max": str(event_cfg.get("event_chapters_max")),
                        "chapters_per_volume": str(event_cfg.get("chapters_per_volume") or "无"),
                    },
                    prompts_dir=prompts_dir,
                    user_data_keys={"volume_arc", "world_hooks", "workshop_volume"},
                )
                response = call_model(prompt)
                eng_path = config_manager.layout.plot_engine_volume_path(volume_num)
                _atomic_write_text(eng_path, f"{str(response).strip()}\n")
                merged = planner.merge_volume_engine_response(
                    volume_num,
                    response,
                    fallback_workshop=workshop,
                    volume_arc_text=volume_arc,
                )
                results["data"] = {
                    "plot_engine": response,
                    "plot_engine_volume_path": str(eng_path),
                    "volume_event_plan": merged.get("plan"),
                    "volume_event_plan_path": merged.get("path"),
                }
                results["status"] = "awaiting_confirmation"
                results["message"] = f"卷 {volume_num} 剧情推演完成，{merged.get('event_count')} 个事件已写入规划。"
                return results

            if scope == "event":
                if not event_id:
                    results["status"] = "error"
                    results["message"] = "scope=event 须指定 event_id"
                    return results
                plan = planner.load_volume_event_plan(volume_num)
                event_card = planner.get_event(plan, str(event_id))
                if not event_card:
                    results["status"] = "blocked"
                    results["message"] = f"事件 {event_id} 不存在，请先 plan_volume_events"
                    return results
                we_path = config_manager.layout.plot_workshop_event_path(volume_num, str(event_id))
                if we_path.exists():
                    workshop_event = json.loads(we_path.read_text(encoding="utf-8"))
                else:
                    workshop_event = plot_workshop.generate_event_workshop(
                        event_card,
                        world_hooks=config_manager.read_text(config_manager.find_file(["world_hooks.md"])),
                        genre=genre or config.get("genre"),
                    )
                    _atomic_write_text(we_path, f"{json.dumps(workshop_event, ensure_ascii=False, indent=2)}\n")
                vol_eng_path = config_manager.layout.plot_engine_volume_path(volume_num)
                template = load_prompt("plot_engine_event")
                prompt = build_task_prompt(
                    template,
                    {
                        "volume_num": str(volume_num),
                        "event_id": str(event_id),
                        "event_card": event_card,
                        "workshop_event": workshop_event,
                        "plot_engine_volume_excerpt": config_manager.read_text(vol_eng_path)[:3000],
                        "character_status": serialize_character_cards(config_manager.load_character_cards()),
                    },
                    prompts_dir=prompts_dir,
                    user_data_keys={
                        "event_card",
                        "workshop_event",
                        "plot_engine_volume_excerpt",
                        "character_status",
                    },
                )
                response = call_model(prompt)
                ee_path = config_manager.layout.plot_engine_event_path(volume_num, str(event_id))
                _atomic_write_text(ee_path, f"{str(response).strip()}\n")
                saved = planner.save_event_outline_from_engine(volume_num, str(event_id), response)
                results["data"] = {
                    "plot_engine": response,
                    "plot_engine_event_path": str(ee_path),
                    "event_outline_path": saved.get("path"),
                }
                results["status"] = "awaiting_confirmation"
                results["message"] = f"事件 {event_id} 推演完成，event_outline 已落盘。"
                return results

            if scope == "chapter" and not event_cfg.get("plot_engine_per_chapter_enabled", False):
                results["status"] = "blocked"
                results["message"] = (
                    "章级 plot_engine 默认关闭（plot_engine_per_chapter_enabled=false）。"
                    "主链请走事件层编排；复杂章可在 config 中开启。"
                )
                return results
            chapter_num = kwargs.get("chapter_num")
            snapshot = config_manager.get_context_snapshot(
                chapter_num=int(chapter_num) if chapter_num is not None else None,
                explicit_current_arc=kwargs.get("current_arc_name"),
            )
            template = load_prompt("plot_engine")
            character_status = (
                kwargs.get("character_status")
                or kwargs.get("characters")
                or serialize_character_cards(snapshot.get("character_cards"))
            )
            prompt = build_task_prompt(
                template,
                {
                    "world_building_hooks": kwargs.get("world_hooks", "") or snapshot.get("world_hooks", ""),
                    "current_progress_node": kwargs.get("progress_node", "") or snapshot.get("progress_node", ""),
                    "character_status": character_status,
                    "volume_core_hook": kwargs.get("volume_core_hook", ""),
                    "trope_hint": kwargs.get("trope_hint", "") or snapshot.get("trope_hint", ""),
                    "workshop_result": kwargs.get("workshop_result") or snapshot.get("plot_workshop", {}),
                    "world_hooks_summary": kwargs.get("world_hooks", "") or snapshot.get("world_hooks", ""),
                },
                prompts_dir=prompts_dir,
                user_data_keys={
                    "world_building_hooks",
                    "world_hooks_summary",
                    "current_progress_node",
                    "character_status",
                    "workshop_result",
                },
                user_data_limits={"world_building_hooks": 10000, "workshop_result": 6000},
            )

            response = call_model(prompt)
            results["data"]["plot_engine"] = response
            plot_engine_name = (
                f"plot_engine_chapter_{int(chapter_num)}.md" if chapter_num is not None else "plot_engine.md"
            )
            plot_engine_path = config_manager.layout.plot_engine_path(plot_engine_name)
            _atomic_write_text(plot_engine_path, f"{str(response).strip()}\n")
            results["data"]["plot_engine_path"] = str(plot_engine_path)
            results["status"] = "awaiting_confirmation"
            results["message"] = "剧情引擎推演完毕，请确认。"

        elif action == "plot_workshop":
            scope = str(kwargs.get("scope") or "chapter").lower()
            per_chapter = config_manager.get_event_config().get("plot_workshop_per_chapter_enabled", False)
            config = config_manager.load_config()
            volume_num = int(kwargs.get("volume_num") or config.get("current_volume", 1))
            event_id = kwargs.get("event_id")
            event_cfg = config_manager.get_event_config()

            if scope == "volume":
                volume_arc = kwargs.get("volume_arc") or config_manager.read_text(
                    config_manager.find_file(["volume_*_outline.md", "volume_arc.md"])
                )
                world_hooks = kwargs.get("world_hooks") or config_manager.read_text(
                    config_manager.find_file(["world_hooks.md"])
                )
                workshop = plot_workshop.generate_volume_workshop(
                    volume_num,
                    volume_arc=volume_arc,
                    world_hooks=world_hooks,
                    event_count=int(kwargs.get("event_count") or event_cfg.get("events_per_volume_default") or 3),
                    event_chapters_min=int(event_cfg.get("event_chapters_min") or 3),
                    event_chapters_max=int(event_cfg.get("event_chapters_max") or 15),
                    genre=genre or config.get("genre"),
                    core_pleasure=core_pleasure or kwargs.get("core_pleasure"),
                )
                if kwargs.get("use_llm") and _model_configured:
                    ws_template = load_prompt("plot_workshop_volume")
                    ws_prompt = build_task_prompt(
                        ws_template,
                        {
                            "volume_num": str(volume_num),
                            "volume_arc": volume_arc,
                            "world_hooks": world_hooks,
                            "event_chapters_min": str(event_cfg.get("event_chapters_min")),
                            "event_chapters_max": str(event_cfg.get("event_chapters_max")),
                            "events_per_volume": str(kwargs.get("event_count") or event_cfg.get("events_per_volume_default")),
                            "workshop_volume_stub": workshop,
                        },
                        prompts_dir=prompts_dir,
                        user_data_keys={"volume_arc", "world_hooks", "workshop_volume_stub"},
                    )
                    try:
                        ws_llm = call_model(ws_prompt)
                        workshop = {**workshop, **extract_json_from_llm(ws_llm), "source": "llm_refined"}
                    except (ValueError, json.JSONDecodeError):
                        pass
                ws_path = config_manager.layout.plot_workshop_volume_path(volume_num)
                _atomic_write_text(ws_path, f"{json.dumps(workshop, ensure_ascii=False, indent=2)}\n")
                results["data"] = {
                    "plot_workshop": workshop,
                    "plot_workshop_path": str(ws_path),
                    "scope": "volume",
                }
                results["message"] = f"卷 {volume_num} 剧情工坊：{len(workshop.get('event_cards', []))} 张事件卡片"
                results["status"] = "awaiting_confirmation"
                return results

            if scope == "event":
                if not event_id:
                    results["status"] = "error"
                    results["message"] = "scope=event 须指定 event_id"
                    return results
                planner = config_manager.get_event_planner()
                plan = planner.load_volume_event_plan(volume_num)
                event_card = planner.get_event(plan, str(event_id))
                if not event_card:
                    results["status"] = "blocked"
                    results["message"] = f"事件 {event_id} 不存在，请先 plan_volume_events"
                    return results
                vol_ws_path = config_manager.layout.plot_workshop_volume_path(volume_num)
                volume_workshop = (
                    json.loads(vol_ws_path.read_text(encoding="utf-8")) if vol_ws_path.exists() else {}
                )
                workshop = plot_workshop.generate_event_workshop(
                    event_card,
                    volume_workshop=volume_workshop,
                    world_hooks=kwargs.get("world_hooks")
                    or config_manager.read_text(config_manager.find_file(["world_hooks.md"])),
                    genre=genre or config.get("genre"),
                )
                if kwargs.get("use_llm") and _model_configured:
                    ev_template = load_prompt("plot_workshop_event")
                    ev_prompt = build_task_prompt(
                        ev_template,
                        {
                            "volume_num": str(volume_num),
                            "event_id": str(event_id),
                            "event_card": event_card,
                            "volume_arc": config_manager.read_text(
                                config_manager.find_file(["volume_*_outline.md", "volume_arc.md"])
                            ),
                            "volume_workshop_constraints": volume_workshop.get("constraints", []),
                            "world_hooks": kwargs.get("world_hooks", ""),
                        },
                        prompts_dir=prompts_dir,
                        user_data_keys={"event_card", "volume_arc", "world_hooks"},
                    )
                    try:
                        ev_llm = call_model(ev_prompt)
                        workshop = {**workshop, **extract_json_from_llm(ev_llm), "source": "llm_refined"}
                    except (ValueError, json.JSONDecodeError):
                        pass
                we_path = config_manager.layout.plot_workshop_event_path(volume_num, str(event_id))
                _atomic_write_text(we_path, f"{json.dumps(workshop, ensure_ascii=False, indent=2)}\n")
                results["data"] = {
                    "plot_workshop": workshop,
                    "plot_workshop_path": str(we_path),
                    "scope": "event",
                }
                results["message"] = f"事件 {event_id} 剧情工坊：{len(workshop.get('scene_beats', []))} 个场景节拍"
                results["status"] = "awaiting_confirmation"
                return results

            if scope == "chapter" and not per_chapter:
                results["status"] = "blocked"
                results["message"] = (
                    "章级 plot_workshop 默认关闭（plot_workshop_per_chapter_enabled=false）。"
                    "主链请走 plan_volume_events → plan_event → chapter_beats；"
                    "复杂章可在 config 中开启章级工坊。"
                )
                return results
            chapter_num = kwargs.get("chapter_num")
            snapshot = config_manager.get_context_snapshot(
                chapter_num=int(chapter_num) if chapter_num is not None else None,
                explicit_current_arc=kwargs.get("current_arc_name"),
            )
            character_status = (
                kwargs.get("character_status")
                or kwargs.get("characters")
                or snapshot.get("character_cards", {})
            )
            workshop_result = plot_workshop.generate_plot(
                progress_node=kwargs.get("progress_node") or snapshot.get("progress_node"),
                character_status=character_status,
                genre=genre or snapshot.get("config", {}).get("genre"),
                core_pleasure=core_pleasure or kwargs.get("core_pleasure"),
                world_hooks=kwargs.get("world_hooks") or snapshot.get("world_hooks"),
                relationship_context=kwargs.get("relationship_context") or snapshot.get("relationship_context"),
                faction_context=kwargs.get("faction_context") or snapshot.get("faction_context"),
                trope_hint=kwargs.get("trope_hint"),
                goal=kwargs.get("goal"),
                chapter_goal=kwargs.get("chapter_goal"),
                target_conflict=kwargs.get("target_conflict"),
                desired_payoff=kwargs.get("desired_payoff"),
                title=kwargs.get("title"),
            )
            plot_workshop_name = (
                f"plot_workshop_chapter_{int(chapter_num)}.json"
                if chapter_num is not None
                else "plot_workshop.json"
            )
            plot_workshop_path = config_manager.layout.plot_engine_path(plot_workshop_name)
            _atomic_write_text(
                plot_workshop_path,
                f"{json.dumps(workshop_result, ensure_ascii=False, indent=2)}\n",
            )
            results["data"] = {
                "plot_workshop": workshop_result,
                "plot_workshop_path": str(plot_workshop_path),
                "snapshot": {
                    "current_arc_name": snapshot.get("current_arc_name"),
                    "progress_node": snapshot.get("progress_node"),
                },
            }
            results["message"] = f"剧情工坊已生成桥段方案：{workshop_result['selected_trope']['name']}"
            results["status"] = "awaiting_confirmation"

        elif action == "write_chapter":
            loop_result = writing_loop.write_chapter(
                chapter_num=int(kwargs.get("chapter_num", 1)),
                mode=mode,
                stage=kwargs.get("stage", "outline"),
                chapter_word_count=chapter_word_count,
                batch_mode=bool(kwargs.get("batch_mode", False)),
                volume_name=kwargs.get("volume_name", ""),
                progress_node=kwargs.get("progress_node", ""),
                prev_summary=kwargs.get("prev_summary", ""),
                prev_ending=kwargs.get("prev_ending", ""),
                characters=kwargs.get("characters", ""),
                voice_config=kwargs.get("voice_config") or config_manager.load_voice_config(),
                trope_hint=kwargs.get("trope_hint"),
                workshop_result=kwargs.get("workshop_result"),
                plot_engine_result=kwargs.get("plot_engine_result"),
                current_arc_name=kwargs.get("current_arc_name"),
                confirmed_outline=kwargs.get("confirmed_outline"),
            )
            results.update(loop_result)

        elif action == "confirm_step":
            chapter_num = int(kwargs.get("chapter_num", 1))
            step = str(kwargs.get("step", "")).strip().lower()
            notes = kwargs.get("notes")

            if step == "outline":
                workflow = config_manager.confirm_outline(
                    chapter_num=chapter_num,
                    outline_text=kwargs.get("outline_text") or kwargs.get("content"),
                    notes=notes,
                )
                results["status"] = "complete"
                results["message"] = f"第 {chapter_num} 章单章大纲已确认。"
                results["data"] = {"workflow": workflow}
            elif step == "draft":
                draft_text = kwargs.get("draft_text") or kwargs.get("content") or ""
                voice_config = kwargs.get("voice_config") or config_manager.load_voice_config()
                validator = StyleValidator(voice_config, strict_mode=False)
                validation = validator.validate(draft_text) if draft_text else {"passed": True, "issues": []}
                word_report = build_word_report(draft_text) if draft_text else {}
                workflow = config_manager.confirm_draft(
                    chapter_num=chapter_num,
                    draft_text=draft_text or None,
                    notes=notes,
                    word_report=word_report or None,
                    validation=validation or None,
                )
                results["status"] = "complete"
                results["message"] = f"第 {chapter_num} 章篇章草稿已确认。"
                results["data"] = {
                    "workflow": workflow,
                    "validation": validation,
                    "word_count": word_report,
                }
            else:
                results["status"] = "error"
                results["message"] = f"Unsupported confirmation step: {step}"

        elif action == "finalize_chapter":
            chapter_num = int(kwargs.get("chapter_num", 1))
            project_state.trigger("before_finalize", chapter_num=chapter_num)
            workflow_gate = config_manager.validate_chapter_workflow(
                chapter_num=chapter_num,
                target_phase="finalize",
            )
            if not workflow_gate["ready"]:
                results["status"] = "blocked"
                results["message"] = format_blocked_message(workflow_gate.get("blockers", []))
                results["data"] = {"workflow": workflow_gate}
                return results

            final_text = kwargs.get("final_text") or workflow_gate["chapter_workflow"].get("draft", {}).get("content", "")
            word_report = build_word_report(final_text)
            word_count = int(kwargs.get("word_count") or word_report["chinese_characters"])

            voice_config = kwargs.get("voice_config") or config_manager.load_voice_config()
            validator = StyleValidator(voice_config, strict_mode=False)
            validation = validator.validate(final_text)

            if validation.get("critical_issues"):
                results["status"] = "blocked"
                results["message"] = format_blocked_message(
                    [item.get("message", "") for item in validation["critical_issues"]]
                )
                results["data"] = {
                    "workflow": workflow_gate,
                    "validation": validation,
                    "word_count": word_report,
                }
                return results

            chapter_title = kwargs.get("title") or _extract_chapter_title(final_text) or f"第{chapter_num}章"
            finalized = phase_runner.run_phase(
                "finalize",
                chapter_num=chapter_num,
                draft=final_text,
                word_count=word_count,
                validation=validation,
                finalization={**(kwargs.get("finalization") or {}), "title": chapter_title},
            )
            results.update(finalized)
            results.setdefault("data", {})
            results["data"]["word_count"] = word_report

            final_path = config_manager.layout.final_dir / f"chapter-{chapter_num:03d}-final.md"
            _atomic_write_text(final_path, f"{final_text.strip()}\n")
            results["data"]["final_path"] = str(final_path)
            
            # ================================================================
            # ✅ 修复：自动触发后续流程
            # ================================================================
            
            # 1. 自动关系更新（如果有角色数据）
            character_updates = kwargs.get("character_updates")
            character_sync_result = None
            if character_updates:
                try:
                    character_sync_result = config_manager.sync_characters_from_chapter(
                        chapter_num=chapter_num,
                        character_updates=character_updates,
                    )
                    results["data"]["character_sync"] = character_sync_result
                except Exception as e:
                    results["data"]["character_sync_error"] = str(e)
            
            # 2. 自动一致性检查
            relationship_validation = None
            try:
                relationship_validation = relationship_validator.validate(chapter_num=chapter_num)
                results["data"]["relationship_validation"] = relationship_validation
            except Exception as e:
                results["data"]["validation_error"] = str(e)
            
            # 3. 自动剧情推荐
            plot_recommendations = None
            try:
                plot_recommendations = plot_recommender.recommend(
                    character_id=kwargs.get("character_id"),
                    chapter_num=chapter_num + 1,
                    focus_types=kwargs.get("focus_types"),
                )
                results["data"]["plot_recommendations"] = plot_recommendations
            except Exception as e:
                results["data"]["recommendation_error"] = str(e)
            
            # ✅ 更新完成消息，包含所有自动流程结果
            validation_status = "✅ 通过" if relationship_validation and relationship_validation.get("valid") else "⚠️ 发现问题"
            rec_count = plot_recommendations.get("count", 0) if plot_recommendations else 0

            # ProjectState 自动同步（与 ConfigManager 共用 schema）
            sync_report = project_state.sync_after_chapter(
                chapter_num=chapter_num,
                chapter_title=chapter_title,
                chapter_text=final_text,
                word_count=word_count,
            )
            results["data"]["project_state_sync"] = sync_report

            results["message"] = (
                f"✅ 第 {chapter_num} 章终稿入库完成\n"
                f"📊 字数：{word_count} 汉字\n"
                f"🔍 关系一致性：{validation_status}\n"
                f"💡 已生成 {rec_count} 个下一章剧情推荐\n"
                f"🔄 项目状态已自动同步"
            )

        elif action == "workflow_audit":
            chapter_num = kwargs.get("chapter_num")
            preflight = config_manager.validate_preflight(
                chapter_num=int(chapter_num) if chapter_num is not None else None,
                explicit_current_arc=kwargs.get("current_arc_name"),
            )
            ps_preflight = (
                project_state.verify_preflight(int(chapter_num))
                if chapter_num is not None
                else {}
            )
            workflow = (
                config_manager.validate_chapter_workflow(
                    chapter_num=int(chapter_num),
                    target_phase=str(kwargs.get("target_phase") or "outline"),
                )
                if chapter_num is not None
                else {}
            )
            results["data"] = preflight
            if ps_preflight:
                results["data"]["project_state_preflight"] = ps_preflight
            if workflow:
                results["data"]["workflow"] = workflow
            results["message"] = "流程审计完成。"
            results["status"] = "complete" if preflight["ready"] and workflow.get("ready", True) else "blocked"

        # ==================== 多卷管理 Actions ====================
        elif action == "check_volume_completion":
            chapter_num = int(kwargs.get("chapter_num", 1))
            volume_status = config_manager.check_volume_completion(chapter_num)
            results["data"] = volume_status
            results["message"] = f"第 {volume_status['current_volume']} 卷检查完成"
            if volume_status.get("should_transition"):
                results["message"] += "，建议流转至下一卷"
            results["status"] = "complete"

        elif action == "transition_volume":
            current_volume = int(
                kwargs.get("current_volume") or config_manager.load_config().get("current_volume", 1)
            )
            transition_result = config_manager.transition_to_next_volume(current_volume)
            results["data"] = transition_result
            if transition_result.get("at_book_end"):
                results["message"] = transition_result["message"]
            else:
                checklist = transition_result.get("checklist") or []
                suffix = f" 下一步：{' → '.join(checklist[:3])}" if checklist else ""
                results["message"] = transition_result["message"] + suffix
            results["status"] = "complete"

        # ==================== 角色卡管理 Actions ====================
        elif action == "get_character":
            character_id = kwargs.get("character_id")
            if not character_id:
                results["status"] = "error"
                results["message"] = "缺少 character_id 参数"
            else:
                character = config_manager.get_character(character_id)
                results["data"] = {"character": character}
                results["message"] = f"获取角色 {character_id} 信息" if character else f"角色 {character_id} 不存在"
                results["status"] = "complete" if character else "not_found"

        elif action == "update_character":
            character_id = kwargs.get("character_id")
            character_data = kwargs.get("character_data", {})
            chapter_num = kwargs.get("chapter_num")
            if not character_id:
                results["status"] = "error"
                results["message"] = "缺少 character_id 参数"
            else:
                updated = config_manager.update_character(character_id, character_data, chapter_num)
                results["data"] = {"character": updated}
                results["message"] = f"角色 {character_id} 更新成功"
                results["status"] = "complete"

        elif action == "list_characters":
            character_cards = config_manager.load_character_cards()
            summary = config_manager.get_character_progress_summary()
            results["data"] = {
                "characters": list(character_cards.get("characters", {}).keys()),
                "summary": summary,
            }
            results["message"] = f"共 {summary['total_characters']} 个角色"
            results["status"] = "complete"

        elif action == "validate_characters":
            chapter_num = int(kwargs.get("chapter_num", 1))
            validation = config_manager.validate_character_consistency(chapter_num)
            results["data"] = validation
            results["message"] = "角色一致性检查完成" if validation["valid"] else "发现角色一致性问题"
            results["status"] = "complete" if validation["valid"] else "warning"

        # ==================== 角色关系管理 Actions (v1.4.0) ====================
        
        elif action == "create_relationship":
            character_a = kwargs.get("character_a")
            character_b = kwargs.get("character_b")
            rel_type = kwargs.get("rel_type")
            metrics = kwargs.get("metrics")
            since_chapter = kwargs.get("since_chapter")
            bidirectional = kwargs.get("bidirectional")
            
            if not character_a or not character_b or not rel_type:
                results["status"] = "error"
                results["message"] = "缺少必需参数：character_a, character_b, rel_type"
            else:
                try:
                    relationship = relationship_manager.create_relationship(
                        character_a=character_a,
                        character_b=character_b,
                        rel_type=rel_type,
                        metrics=metrics,
                        since_chapter=since_chapter,
                        bidirectional=bidirectional,
                    )
                    results["data"] = {"relationship": relationship}
                    results["message"] = f"创建关系：{character_a} ↔ {character_b} ({rel_type})"
                    results["status"] = "complete"
                except ValueError as e:
                    results["status"] = "error"
                    results["message"] = str(e)
        
        elif action == "update_relationship":
            character_a = kwargs.get("character_a")
            character_b = kwargs.get("character_b")
            metrics_change = kwargs.get("metrics_change")
            event = kwargs.get("event", "")
            chapter_num = kwargs.get("chapter_num")
            rel_type = kwargs.get("rel_type")
            
            if not character_a or not character_b:
                results["status"] = "error"
                results["message"] = "缺少必需参数：character_a, character_b"
            else:
                try:
                    relationship = relationship_manager.update_relationship(
                        character_a=character_a,
                        character_b=character_b,
                        metrics_change=metrics_change,
                        event=event,
                        chapter_num=chapter_num,
                        rel_type=rel_type,
                    )
                    results["data"] = {"relationship": relationship}
                    results["message"] = f"更新关系：{character_a} ↔ {character_b}"
                    results["status"] = "complete"
                except ValueError as e:
                    results["status"] = "error"
                    results["message"] = str(e)
        
        elif action == "get_relationship":
            character_a = kwargs.get("character_a")
            character_b = kwargs.get("character_b")
            
            if not character_a or not character_b:
                results["status"] = "error"
                results["message"] = "缺少必需参数：character_a, character_b"
            else:
                relationship = relationship_manager.get_relationship(character_a, character_b)
                results["data"] = {"relationship": relationship}
                results["message"] = f"获取关系：{character_a} ↔ {character_b}" if relationship else f"关系不存在：{character_a} ↔ {character_b}"
                results["status"] = "complete" if relationship else "not_found"
        
        elif action == "list_relationships":
            character_id = kwargs.get("character_id")
            rel_type = kwargs.get("rel_type")
            status = kwargs.get("status")
            
            relationships = relationship_manager.list_relationships(
                character_id=character_id,
                rel_type=rel_type,
                status=status,
            )
            results["data"] = {
                "relationships": relationships,
                "count": len(relationships),
            }
            results["message"] = f"共 {len(relationships)} 个关系"
            results["status"] = "complete"
        
        elif action == "delete_relationship":
            character_a = kwargs.get("character_a")
            character_b = kwargs.get("character_b")
            
            if not character_a or not character_b:
                results["status"] = "error"
                results["message"] = "缺少必需参数：character_a, character_b"
            else:
                success = relationship_manager.delete_relationship(character_a, character_b)
                results["data"] = {"deleted": success}
                results["message"] = f"删除关系：{character_a} ↔ {character_b}" if success else "关系不存在"
                results["status"] = "complete" if success else "not_found"
        
        elif action == "get_character_relationships":
            character_id = kwargs.get("character_id")
            
            if not character_id:
                results["status"] = "error"
                results["message"] = "缺少必需参数：character_id"
            else:
                relationships = relationship_manager.get_character_relationships(character_id)
                results["data"] = {
                    "character_id": character_id,
                    "relationships": relationships,
                    "count": len(relationships),
                }
                results["message"] = f"角色 {character_id} 有 {len(relationships)} 个关系"
                results["status"] = "complete"
        
        # 阵营管理
        elif action == "create_faction":
            name = kwargs.get("name")
            faction_type = kwargs.get("faction_type")
            members = kwargs.get("members", [])
            enemies = kwargs.get("enemies")
            allies = kwargs.get("allies")
            hierarchy = kwargs.get("hierarchy")
            
            if not name or not faction_type:
                results["status"] = "error"
                results["message"] = "缺少必需参数：name, faction_type"
            else:
                try:
                    faction = relationship_manager.create_faction(
                        name=name,
                        faction_type=faction_type,
                        members=members,
                        enemies=enemies,
                        allies=allies,
                        hierarchy=hierarchy,
                    )
                    results["data"] = {"faction": faction}
                    results["message"] = f"创建阵营：{name}"
                    results["status"] = "complete"
                except ValueError as e:
                    results["status"] = "error"
                    results["message"] = str(e)
        
        elif action == "get_faction":
            faction_id = kwargs.get("faction_id")
            
            if not faction_id:
                results["status"] = "error"
                results["message"] = "缺少必需参数：faction_id"
            else:
                faction = relationship_manager.get_faction(faction_id)
                results["data"] = {"faction": faction}
                results["message"] = f"获取阵营：{faction_id}" if faction else f"阵营不存在：{faction_id}"
                results["status"] = "complete" if faction else "not_found"
        
        elif action == "list_factions":
            factions = relationship_manager.list_factions()
            results["data"] = {
                "factions": factions,
                "count": len(factions),
            }
            results["message"] = f"共 {len(factions)} 个阵营"
            results["status"] = "complete"
        
        elif action == "add_faction_member":
            faction_id = kwargs.get("faction_id")
            character_id = kwargs.get("character_id")
            role = kwargs.get("role", "member")
            
            if not faction_id or not character_id:
                results["status"] = "error"
                results["message"] = "缺少必需参数：faction_id, character_id"
            else:
                try:
                    faction = relationship_manager.add_faction_member(
                        faction_id=faction_id,
                        character_id=character_id,
                        role=role,
                    )
                    results["data"] = {"faction": faction}
                    results["message"] = f"添加 {character_id} 到阵营 {faction_id} ({role})"
                    results["status"] = "complete"
                except ValueError as e:
                    results["status"] = "error"
                    results["message"] = str(e)
        
        # 关系一致性检查
        elif action == "validate_relationships":
            chapter_num = int(kwargs.get("chapter_num", 1))
            check_types = kwargs.get("check_types")
            
            validation = relationship_validator.validate(
                chapter_num=chapter_num,
                check_types=check_types,
            )
            results["data"] = validation
            results["message"] = "关系一致性检查完成" if validation["valid"] else "发现关系一致性问题"
            results["status"] = "complete" if validation["valid"] else "warning"
        
        elif action == "detect_conflicts":
            character_id = kwargs.get("character_id")
            
            conflicts = relationship_validator.detect_conflicts(character_id=character_id)
            results["data"] = {
                "conflicts": conflicts,
                "count": len(conflicts),
            }
            results["message"] = f"检测到 {len(conflicts)} 个潜在冲突"
            results["status"] = "complete"
        
        elif action == "get_relationship_network":
            network = relationship_manager.get_relationship_network()
            results["data"] = network
            results["message"] = f"关系网络：{network['stats']['total_characters']} 角色，{network['stats']['total_relationships']} 关系，{network['stats']['total_factions']} 阵营"
            results["status"] = "complete"
        
        # 剧情推荐 (v1.4.0)
        elif action == "recommend_plot":
            character_id = kwargs.get("character_id")
            chapter_num = int(kwargs.get("chapter_num", 1))
            focus_types = kwargs.get("focus_types")
            
            recommendations = plot_recommender.recommend(
                character_id=character_id,
                chapter_num=chapter_num,
                focus_types=focus_types,
            )
            results["data"] = recommendations
            results["message"] = f"生成 {recommendations['count']} 个剧情推荐"
            results["status"] = "complete"
        
        elif action == "generate_scene_outline":
            recommendation = kwargs.get("recommendation", {})
            context = kwargs.get("context", {})
            
            if not recommendation:
                results["status"] = "error"
                results["message"] = "缺少必需参数：recommendation"
            else:
                outline = plot_recommender.generate_scene_outline(
                    recommendation=recommendation,
                    context=context,
                )
                results["data"] = {"scene_outline": outline}
                results["message"] = f"生成场景大纲：{outline.get('title', '未命名')}"
                results["status"] = "complete"

    except Exception as e:
        results["status"] = "error"
        results["message"] = f"Error: {str(e)}"

    return results


def get_required_confirmations(action: str) -> list:
    confirmations = {
        "init": ["小说基本信息"],
        "confirm_pre_init": ["Pre-Init 节拍表确认"],
        "world_hooks": ["世界观爽点预埋"],
        "voice_config": ["声音配置（voice_config）"],
        "plan_book_volumes": ["全书卷规划"],
        "volume_arc": ["卷情绪弧"],
        "plan_volume_events": ["卷内事件清单"],
        "plan_event": ["单事件纲"],
        "chapter_beats": ["章节节拍表"],
        "plot_engine": ["剧情推演结果确认"],  # ✅ 修复：添加确认
        "plot_workshop": ["剧情工坊桥段方案确认"],
        "write_chapter": ["单章大纲"],
        "confirm_step": ["单章大纲确认", "单章正文确认"],
        "finalize_chapter": [],
        "workflow_audit": ["流程审计结果"],
        # 多卷管理
        "check_volume_completion": ["卷完成状态"],
        "transition_volume": ["卷流转确认"],
        # 角色卡管理
        "get_character": ["角色信息"],
        "update_character": ["角色更新确认"],
        "list_characters": ["角色列表"],
        "validate_characters": ["角色一致性检查结果"],
        # 角色关系管理 (v1.4.0)
        "create_relationship": ["关系创建确认"],
        "update_relationship": ["关系更新确认"],
        "delete_relationship": ["关系删除确认"],
        "create_faction": ["阵营创建确认"],
        "add_faction_member": ["阵营成员添加确认"],
        "validate_relationships": ["关系一致性检查结果"],
        "detect_conflicts": ["关系冲突检测结果"],
        # 剧情推荐 (v1.4.0)
        "recommend_plot": ["剧情推荐结果"],
        "generate_scene_outline": ["场景大纲确认"],
    }
    return confirmations.get(action, [])
