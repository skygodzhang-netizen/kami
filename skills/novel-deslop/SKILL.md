---
name: novel-deslop
description: 仅处理小说章节的去 AI 味、重复、翻译腔和修辞堆砌。若用户重点要求“增加人味”、人物对话或情绪余波、改善“说明书式”叙述，优先选 novel-human-texture；不用于邮件、报告、闲鱼文案或配置。
---

# Novel Deslop — expression-only adapter

Source: `tance-mang/chinese-webnovel-skills`, commit `ecf552f6930e769d8bbf17818ad3d5a864a7a70b`, upstream `skills/deslop/SKILL.md`, MIT © 2026 tance-mang. Read `references/upstream-SKILL.md` and its cited references for the original editing method.

Apply only inside an explicitly identified `workspace/novels/<book>/` project. The upstream method edits repetition, metaphor, exposition, punctuation and rhythm. First check the raw draft against project canon and continuity. Preserve the raw draft. Write a separate humanized candidate. Keep length near 85–115% of raw unless the user explicitly accepts a justified exception. Do not publish or send text externally.

Hard boundary: change expression only. Do not change names, ages, realms, powers, inventory, location, injury, relationships, knowledge, event causality, timeline, foreshadowing or chapter hook facts. Do not add characters, plot events, revelations or new foreshadowing. Recheck these fields after editing and reject a candidate with any factual difference. Use the current OpenClaw/Agnes model only. Do not run WebNovel Studio CLI or load its API configuration.
