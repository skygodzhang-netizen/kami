---
name: novel-human-texture
description: 用户要求小说正文“增加人味”、改善人物对话/情绪余波或把“说明书式”叙述写自然时选用。先检查项目 canon 再编辑；只改变表达，不处理普通生产文本。
---

# Novel Human Texture — canon-preserving adapter

Source: `tance-mang/chinese-webnovel-skills`, commit `ecf552f6930e769d8bbf17818ad3d5a864a7a70b`, upstream `skills/human/SKILL.md`, MIT © 2026 tance-mang. Read `references/upstream-SKILL.md`, `references/human-texture.md` and `references/sentence-rhythm.md` for the original method.

Work only inside an identified `workspace/novels/<book>/` project after the raw chapter passes canon and continuity checks. Preserve raw. Produce a separate candidate. Improve natural dialogue, restraint, subtext, subtle gestures, hesitation and emotional aftermath only where they fit each character's existing personality and situation. Keep third-person viewpoint and project style. Do not deliberately add typos, grammatical errors, random slang or broken logic to imitate a human.

Some upstream examples propose new irrational acts or escalating conflict. For this production adapter, **do not apply those suggestions when they would alter plot facts**. Do not change names, identity, ages, realm, power, items, location, injuries, knowledge, relationship, timeline, causality, resolved/unresolved hooks, death status, or chapter ending. Do not add or remove events, characters or reveals. Keep candidate length near 85–115% of raw. Run a structured canon diff after revision; reject any factual drift. Do not use WebNovel Studio CLI, API config, third-party provider, global Memory or external publishing.
