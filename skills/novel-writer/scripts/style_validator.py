import re
from typing import Any, Dict, List


SUMMARY_MARKERS = (
    "章节信息总结",
    "章节总结",
    "本章总结",
    "本章信息",
    "章节要点",
    "本章要点",
    "作者备注",
    "下一步计划",
)


def strip_trailing_chapter_summary(text: str) -> str:
    """去除章节末尾的总结/备注"""
    if not text:
        return ""
    content = str(text).rstrip()
    cut_index = -1
    for marker in SUMMARY_MARKERS:
        index = content.rfind(marker)
        if index > cut_index:
            cut_index = index
    if cut_index >= 0 and cut_index >= int(len(content) * 0.6):
        return content[:cut_index].rstrip()
    return content


def count_chinese_characters(text: str) -> int:
    if not text:
        return 0
    body = strip_trailing_chapter_summary(text)
    return len(re.findall(r"[\u4e00-\u9fff]", body))


def build_word_report(text: str) -> Dict[str, Any]:
    if not text:
        return {
            "chinese_characters": 0,
            "digits": 0,
            "latin_words": 0,
            "effective_total": 0,
        }
    body = strip_trailing_chapter_summary(text)
    chinese_characters = len(re.findall(r"[\u4e00-\u9fff]", body))
    digits = len(re.findall(r"\d", body))
    latin_words = len(re.findall(r"[A-Za-z]+", body))
    return {
        "chinese_characters": chinese_characters,
        "digits": digits,
        "latin_words": latin_words,
        "effective_total": chinese_characters + digits + latin_words,
    }


def count_text_units(text: str) -> int:
    return build_word_report(text)["chinese_characters"]


class StyleValidator:
    """
    风格校验器（网文实战配置适配版）
    原则：宽松校验，只检查底线错误，不强制量化指标
    """
    def __init__(self, style_rules: Dict[str, Any] | None = None, strict_mode: bool = False):
        """
        strict_mode: False=宽松模式（推荐），True=严格模式（仅调试）
        """
        self.strict_mode = strict_mode
        style_rules = style_rules or {}
        
        # 新配置：弹性区间，不强制
        guards = style_rules.get("style_guards", {}).get("fragmentation_control", {})
        quality_thresholds = style_rules.get("quality_thresholds", {})
        
        # 段落字数：新配置20-200自然长度，宽松模式下不强制检查
        self.min_words_per_paragraph = int(guards.get("min_words_per_paragraph", 20))  # 从12改为20
        self.max_words_per_paragraph = int(guards.get("max_words_per_paragraph", 200))  # 从150改为200
        
        # 短句检查：宽松模式下放宽
        self.max_consecutive_short_sentences = int(guards.get("max_consecutive_short_sentences", 3 if strict_mode else 5))
        self.short_sentence_threshold = int(style_rules.get("short_sentence_threshold", 15))
        
        # 单句成段：宽松模式下放宽
        self.max_consecutive_single_sentence_paragraphs = int(
            style_rules.get("max_consecutive_single_sentence_paragraphs", 3 if strict_mode else 5)
        )
        
        # 章节字数：新配置2000-5000弹性
        self.min_chapter_words = self._to_int(quality_thresholds.get("min_chapter_words")) or (2000 if strict_mode else None)
        self.target_chapter_words = self._to_int(quality_thresholds.get("target_chapter_words"))
        self.max_chapter_words = self._to_int(quality_thresholds.get("max_chapter_words")) or (5000 if strict_mode else None)
        humanity_signals = style_rules.get("humanity_signals", {})
        repetition_control = style_rules.get("style_guards", {}).get("repetition_control", {})

        self.abstract_emotion_words = humanity_signals.get(
            "abstract_emotion_words",
            ["难过", "悲伤", "痛苦", "愤怒", "愤恨", "孤独", "绝望", "委屈", "温柔", "崩溃", "紧张", "害怕"],
        )
        self.explanation_markers = humanity_signals.get(
            "explanation_markers",
            ["因为", "所以", "其实", "原来", "这让他", "这让她", "他知道", "她知道", "他明白", "她明白", "意味着"],
        )
        tracked_phrases = repetition_control.get("tracked_phrases", [])
        default_cliches = ["倒吸一口凉气", "瞳孔一缩", "心头一震", "恐怖如斯", "不由得", "五味杂陈"]
        self.cliche_phrases = list(dict.fromkeys(default_cliches + tracked_phrases))
        self.max_abstract_emotion_density = float(humanity_signals.get("max_abstract_emotion_per_1k", 6))
        self.max_explanation_density = float(humanity_signals.get("max_explanation_per_1k", 10))
        self.author_signature = style_rules.get("author_signature", {}) or {}
        self.mature_content = self.author_signature.get("mature_content", {}) or {}
        self.mature_content_policy = style_rules.get("mature_content_policy", {}) or {}
        self.meta_narration_patterns = [
            r"第[0-9一二三四五六七八九十百千万两零〇]+[章节卷篇]",
            r"本章",
            r"这一章",
            r"上一章",
            r"下一章",
            r"上章",
            r"下章",
            r"本卷",
            r"下一卷",
            r"上一卷",
            r"卷末",
            r"篇章",
            r"上一篇",
            r"下一篇",
        ]

    def validate(self, text: str) -> Dict[str, Any]:
        normalized_text = strip_trailing_chapter_summary(text or "")
        paragraphs = [item.strip() for item in re.split(r"\n\s*\n", normalized_text) if item.strip()]
        
        issues: List[Dict[str, Any]] = []
        critical_issues: List[Dict[str, Any]] = []  # 新增：底线错误
        paragraph_lengths: List[int] = []
        
        # 英文检查（警告级别）
        # 排除常见的英文标点、数字格式、以及合理的英文术语
        excluded_patterns = [
            r"\d+[a-zA-Z]*",  # 数字开头的混合文本（如 3D, 4K）
            r"[IVXLC]+",      # 罗马数字
        ]
        english_hits = re.findall(r"\b[a-zA-Z]{3,}\b", normalized_text)
        # 过滤掉合理的技术术语和常见缩写
        common_terms = {"AI", "NPC", "BOSS", "VIP", "ID", "OK", "VS", "APP", "URL", "API"}
        filtered_hits = [hit for hit in english_hits if hit not in common_terms]
        if filtered_hits:
            issues.append(
                {
                    "code": "english_detected",
                    "message": f"检测到英文片段：{', '.join(sorted(set(filtered_hits))[:5])}",
                    "severity": "warning",
                }
            )

        if "{{" in normalized_text or "}}" in normalized_text:
            critical_issues.append(
                {
                    "code": "unresolved_prompt_placeholder",
                    "message": "正文中残留未替换的 Prompt 变量，占位符未清理干净",
                    "severity": "critical",
                }
            )
        
        word_report = build_word_report(normalized_text)
        total_units = max(word_report["chinese_characters"], 1)
        abstract_emotion_hits = self._count_phrase_hits(normalized_text, self.abstract_emotion_words)
        explanation_hits = self._count_phrase_hits(normalized_text, self.explanation_markers)
        cliche_hits = self._find_cliche_hits(normalized_text)
        meta_narration_hits = self._find_meta_narration_hits(normalized_text)
        abstract_emotion_density = round(abstract_emotion_hits * 1000 / total_units, 2)
        explanation_density = round(explanation_hits * 1000 / total_units, 2)

        if abstract_emotion_density > self.max_abstract_emotion_density:
            issues.append(
                {
                    "code": "abstract_emotion_overuse",
                    "message": f"抽象情绪词偏多（每千字约 {abstract_emotion_density} 次），建议改成动作、停顿和反应",
                    "severity": "warning",
                }
            )

        if explanation_density > self.max_explanation_density:
            issues.append(
                {
                    "code": "over_explained_emotion",
                    "message": f"解释性连接词偏多（每千字约 {explanation_density} 次），情绪容易写成说明文",
                    "severity": "warning",
                }
            )

        if cliche_hits:
            issues.append(
                {
                    "code": "stale_expression",
                    "message": f"检测到陈词滥调：{', '.join(cliche_hits[:5])}",
                    "severity": "warning",
                }
            )

        if meta_narration_hits:
            issues.append(
                {
                    "code": "meta_narration_detected",
                    "message": f"正文出现管理层词汇：{', '.join(meta_narration_hits[:5])}，需要改成场景、时间或关系表达",
                    "severity": "warning",
                }
            )

        # 段落分析
        consecutive_single_sentence_paragraphs = 0
        max_single_sentence_paragraphs = 0
        sentence_lengths: List[int] = []
        short_sentence_streak = 0
        max_short_sentence_streak = 0

        for index, paragraph in enumerate(paragraphs, start=1):
            length = count_text_units(paragraph)
            paragraph_lengths.append(length)
            
            # 严格模式下检查段落长度
            if self.strict_mode:
                if length < self.min_words_per_paragraph:
                    issues.append(
                        {
                            "code": "paragraph_too_short",
                            "message": f"第 {index} 段字数不足 {self.min_words_per_paragraph}",
                            "severity": "warning",
                        }
                    )
                if length > self.max_words_per_paragraph:
                    issues.append(
                        {
                            "code": "paragraph_too_long",
                            "message": f"第 {index} 段字数超过 {self.max_words_per_paragraph}",
                            "severity": "warning",
                        }
                    )

            sentences = self._split_sentences(paragraph)
            if len(sentences) <= 1:
                consecutive_single_sentence_paragraphs += 1
                max_single_sentence_paragraphs = max(
                    max_single_sentence_paragraphs,
                    consecutive_single_sentence_paragraphs,
                )
            else:
                consecutive_single_sentence_paragraphs = 0

            for sentence in sentences:
                sentence_length = count_text_units(sentence)
                sentence_lengths.append(sentence_length)
                if sentence_length <= self.short_sentence_threshold:
                    short_sentence_streak += 1
                    max_short_sentence_streak = max(max_short_sentence_streak, short_sentence_streak)
                else:
                    short_sentence_streak = 0

        # 短句检查（严格模式）
        if self.strict_mode and max_short_sentence_streak > self.max_consecutive_short_sentences:
            issues.append(
                {
                    "code": "too_many_short_sentences",
                    "message": f"连续短句达到 {max_short_sentence_streak} 次",
                    "severity": "warning",
                }
            )

        # 单句成段检查（严格模式）
        if self.strict_mode and max_single_sentence_paragraphs > self.max_consecutive_single_sentence_paragraphs:
            issues.append(
                {
                    "code": "too_many_single_sentence_paragraphs",
                    "message": f"连续单句成段达到 {max_single_sentence_paragraphs} 次",
                    "severity": "warning",
                }
            )

        # 钩子结尾检查（底线，始终检查）
        if not self._has_hook_ending(paragraphs[-1] if paragraphs else ""):
            critical_issues.append(
                {
                    "code": "weak_hook_ending",
                    "message": "结尾未通过「简洁有力 + 悬念钩子」检查（新配置强制要求）",
                    "severity": "critical",
                }
            )

        # 章节字数检查（严格模式或底线）
        if self.min_chapter_words is not None and word_report["chinese_characters"] < self.min_chapter_words:
            severity = "critical" if word_report["chinese_characters"] < 1500 else "warning"
            (critical_issues if severity == "critical" else issues).append(
                {
                    "code": "chapter_too_short",
                    "message": f"正文汉字数 {word_report['chinese_characters']} 低于下限 {self.min_chapter_words}",
                    "severity": severity,
                }
            )

        if self.max_chapter_words is not None and word_report["chinese_characters"] > self.max_chapter_words:
            issues.append(
                {
                    "code": "chapter_too_long",
                    "message": f"正文汉字数 {word_report['chinese_characters']} 超过上限 {self.max_chapter_words}",
                    "severity": "warning",
                }
            )

        metrics = {
            "word_report": word_report,
            "paragraph_count": len(paragraphs),
            "paragraph_lengths": paragraph_lengths,
            "max_consecutive_short_sentences": max_short_sentence_streak,
            "max_consecutive_single_sentence_paragraphs": max_single_sentence_paragraphs,
            "avg_sentence_length": round(sum(sentence_lengths) / len(sentence_lengths), 2) if sentence_lengths else 0,
            "english_hits": sorted(set(english_hits)),
            "abstract_emotion_hits": abstract_emotion_hits,
            "abstract_emotion_density_per_1k": abstract_emotion_density,
            "explanation_hits": explanation_hits,
            "explanation_density_per_1k": explanation_density,
            "cliche_hits": cliche_hits,
            "meta_narration_hits": meta_narration_hits,
        }
        metrics["chapter_word_limits"] = {
            "min": self.min_chapter_words,
            "target": self.target_chapter_words,
            "max": self.max_chapter_words,
        }

        issues.extend(self._mature_content_policy_reminders(normalized_text))

        # 新配置：passed逻辑 - 只有critical_issues才阻断
        return {
            "passed": not critical_issues,
            "issues": issues,
            "critical_issues": critical_issues,
            "metrics": metrics,
            "strict_mode": self.strict_mode,
        }

    def _mature_content_policy_reminders(self, text: str) -> List[Dict[str, Any]]:
        """按 author_signature.mature_content 做政策提醒，不阻断 passed。"""
        if not self.mature_content.get("enabled"):
            return []
        level = str(self.mature_content.get("level", "mild")).lower()
        if level in ("off", "none", "disabled"):
            return []
        reminders: List[Dict[str, Any]] = []
        boundaries = self.mature_content.get("boundaries") or []
        if boundaries:
            reminders.append(
                {
                    "code": "mature_content_policy",
                    "message": f"擦边政策（{level}）：{'；'.join(str(b) for b in boundaries[:3])}",
                    "severity": "info",
                }
            )
        if level == "mild":
            explicit_markers = ("赤裸", "裸体", "插入", "高潮", "精液", "阴道", "阴茎")
            hits = [m for m in explicit_markers if m in (text or "")]
            if hits:
                reminders.append(
                    {
                        "code": "mature_content_explicit_hint",
                        "message": f"检测到可能超出 mild 级别的直白用词：{', '.join(hits[:3])}，建议改为暗示留白",
                        "severity": "info",
                    }
                )
        return reminders

    def _split_sentences(self, paragraph: str) -> List[str]:
        parts = re.split(r"[。！？!?；;…]+", paragraph)
        return [item.strip("，,：:、 \t\r\n") for item in parts if item.strip()]

    def _has_hook_ending(self, paragraph: str) -> bool:
        """检查结尾是否有钩子：短段 + 悬念/未闭合信号"""
        if not paragraph:
            return False
        ending_length = count_text_units(paragraph)
        if ending_length > 150:
            return False

        strong_markers = (
            "？", "！", "……", "吗", "呢", "吧",
            "忽然", "就在这时", "下一瞬", "却在这时",
            "门被", "电话", "消息", "声音", "脚步",
        )
        if any(marker in paragraph for marker in strong_markers):
            return True

        soft_markers = ("却", "但", "然而", "不料", "竟然", "居然")
        tail = paragraph[-40:] if len(paragraph) > 40 else paragraph
        return any(marker in tail for marker in soft_markers)

    def _to_int(self, value: Any) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _count_phrase_hits(self, text: str, phrases: List[str]) -> int:
        total = 0
        for phrase in phrases:
            if not phrase:
                continue
            total += len(re.findall(re.escape(phrase), text))
        return total

    def _find_cliche_hits(self, text: str) -> List[str]:
        hits: List[str] = []
        for phrase in self.cliche_phrases:
            if phrase and phrase in text:
                hits.append(phrase)
        return hits

    def _find_meta_narration_hits(self, text: str) -> List[str]:
        hits: List[str] = []
        for pattern in self.meta_narration_patterns:
            for match in re.findall(pattern, text):
                if match not in hits:
                    hits.append(match)
        return hits
