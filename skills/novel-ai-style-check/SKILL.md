---
name: novel-ai-style-check
description: 仅在用户要求诊断小说章节正文的机械句式、重复、节奏、说明过多或网文“AI 味”时使用；这是写作特征启发式，不是作者身份鉴定。
---

# Novel AI Style Check — heuristic adapter

Source: `tance-mang/chinese-webnovel-skills`, commit `ecf552f6930e769d8bbf17818ad3d5a864a7a70b`, upstream `skills/aidetect/SKILL.md`, MIT © 2026 tance-mang. Read `references/upstream-SKILL.md` and `references/ai-detector.md` for the upstream checklist.

Only inspect an identified `workspace/novels/<book>/` chapter or creative passage. Diagnose template phrases, repeated structures, metaphor density, paragraph uniformity, repeated emotion words, sentence rhythm, exposition and reading friction. Report concrete excerpts and rough counts, with raw and after-edit observations. Scores are subjective style heuristics. Never claim to identify human or AI authorship, evade a detector, guarantee a “human rate,” or prove platform acceptance. A good reader experience takes priority over minimizing a number.

Read-only: do not edit the draft, canon, Memory or provider config. Do not upload text or call WebNovel Studio CLI/API. Use current OpenClaw/Agnes only. At most two complete humanization cycles; stop when readability is acceptable.
